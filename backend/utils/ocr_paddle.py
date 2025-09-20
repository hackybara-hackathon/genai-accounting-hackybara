from __future__ import annotations
from typing import Dict, List, Optional
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import io, re, os, time
import logging

# =============== CONFIG / DEBUG ===============
DEBUG = True  # turn off later
DEBUG_DIR = "debug_ocr"  # folder to save debug images

if DEBUG:
    os.makedirs(DEBUG_DIR, exist_ok=True)
logging.getLogger("ppocr").setLevel(logging.ERROR)

# =============== PDF -> images ===============
def _pdf_bytes_to_images_pdf2image(file_bytes: bytes) -> List[Image.Image]:
    from pdf2image import convert_from_bytes
    # High DPI helps tiny text
    return convert_from_bytes(
        file_bytes,
        fmt="png",
        dpi=300,
        first_page=1,
        last_page=3
    )

def _pdf_bytes_to_images_pymupdf(file_bytes: bytes) -> List[Image.Image]:
    import fitz  # PyMuPDF
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images: List[Image.Image] = []
    for i, page in enumerate(doc):
        if i >= 3:
            break
        # ~288 dpi render
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(alpha=False, matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    doc.close()
    return images

def _bytes_to_images(file_bytes: bytes) -> List[Image.Image]:
    if file_bytes[:4] == b"%PDF":
        try:
            return _pdf_bytes_to_images_pdf2image(file_bytes)
        except Exception:
            return _pdf_bytes_to_images_pymupdf(file_bytes)
    return [Image.open(io.BytesIO(file_bytes)).convert("RGB")]

# =============== Preprocess ===============
def _preprocess(pil_img: Image.Image) -> np.ndarray:
    """Upscale + grayscale + adaptive threshold + light sharpen."""
    import cv2
    img = np.array(pil_img)  # RGB
    h, w = img.shape[:2]
    # upscale small images
    if max(h, w) < 1200:
        scale = 1200.0 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thr = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 15
    )
    blur = cv2.GaussianBlur(thr, (0, 0), 1.0)
    sharp = cv2.addWeighted(thr, 1.5, blur, -0.5, 0)
    proc = cv2.cvtColor(sharp, cv2.COLOR_GRAY2RGB)
    return proc

# =============== OCR singleton ===============
_OCR: Optional[PaddleOCR] = None
def _get_ocr() -> PaddleOCR:
    global _OCR
    if _OCR is None:
        # angle cls on; slightly relax detection thresholds for thin fonts
        _OCR = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            det_db_box_thresh=0.4,     # default ~0.6; lower finds more boxes
            det_db_thresh=0.25,        # binarization threshold
            det_db_unclip_ratio=1.6,   # expand boxes a bit
        )
    return _OCR

# =============== Result parser ===============
def _extract_lines(result) -> List[str]:
    """
    Handle PaddleOCR outputs across versions:
    - Legacy: [[ [bbox, (text, conf)], ... ]]
    - New:    [ {'data': [ {'text': '...'}, ... ]}, ... ]
    - Flat:   [ {'text': '...','confidence':...}, ... ]
    """
    lines: List[str] = []
    if not result:
        if DEBUG:
            print("DEBUG: OCR result is None or empty")
        return lines
    
    if DEBUG:
        print(f"DEBUG: OCR result type: {type(result)}")
        print(f"DEBUG: OCR result length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
        if result and len(result) > 0:
            print(f"DEBUG: First element type: {type(result[0])}")
            print(f"DEBUG: First few elements: {str(result)[:500]}...")

    # PaddleOCR 3.2.0+ format - check for 'rec_texts' field first
    if isinstance(result, list) and result and isinstance(result[0], dict) and "rec_texts" in result[0]:
        for page in result:
            rec_texts = page.get("rec_texts", [])
            if isinstance(rec_texts, list):
                lines.extend([str(text) for text in rec_texts if text])
        return lines

    # legacy format
    if isinstance(result, list) and result and isinstance(result[0], list):
        for item in result[0]:
            try:
                lines.append(item[1][0])
            except Exception:
                pass
        return lines

    # list of dict pages with 'data'
    if isinstance(result, list) and isinstance(result[0], dict) and "data" in result[0]:
        for page in result:
            for det in page.get("data", []):
                txt = det.get("text") or det.get("text_raw") or ""
                if txt:
                    lines.append(txt)
        return lines

    # flat list of dicts with 'text'
    if isinstance(result, list) and isinstance(result[0], dict) and "text" in result[0]:
        for det in result:
            txt = det.get("text") or det.get("text_raw") or ""
            if txt:
                lines.append(txt)
        return lines

    return lines

# =============== Public API ===============
def ocr_image(file_bytes: bytes) -> Dict:
    ocr = _get_ocr()
    images = _bytes_to_images(file_bytes)

    ts = time.strftime("%Y%m%d-%H%M%S")
    page_texts: List[str] = []

    for idx, pil_img in enumerate(images, start=1):
        # save raw input for this page
        if DEBUG:
            pil_img.save(os.path.join(DEBUG_DIR, f"{ts}_p{idx}_input.png"))

        arr = _preprocess(pil_img)

        # save preprocessed preview
        if DEBUG:
            Image.fromarray(arr).save(os.path.join(DEBUG_DIR, f"{ts}_p{idx}_preproc.png"))

        # run OCR with proper error handling
        try:
            result = ocr.ocr(arr, cls=True)  # cls=True for text angle detection
        except Exception as e:
            print(f"Warning: OCR with cls=True failed: {e}")
            try:
                result = ocr.ocr(arr)  # fallback without cls parameter
            except Exception as e2:
                print(f"Error: OCR failed completely: {e2}")
                result = None

        if DEBUG:
            # also dump the raw python structure for debugging
            with open(os.path.join(DEBUG_DIR, f"{ts}_p{idx}_raw.txt"), "w", encoding="utf-8") as f:
                f.write(repr(result)[:200000])

        lines = _extract_lines(result) if result else []
        page_texts.append("\n".join(lines))

    full_text = "\n\n".join(page_texts).strip()
    amounts = [float(m.replace(",", "")) for m in re.findall(r"\d{1,3}(?:,\d{3})*\.\d{2}", full_text)]
    approx_total = max(amounts) if amounts else None

    return {
        "engine": "paddleocr",
        "pages": len(images),
        "text": full_text,
        "approx_total": approx_total,
        "debug_saved": DEBUG,
        "debug_dir": DEBUG_DIR if DEBUG else None,
    }

# =============== Heuristic field parsing ===============
_DATE_PAT = re.compile(
    r"\b(20\d{2}|19\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])\b"
    r"|"
    r"\b(0?[1-9]|[12]\d|3[01])[-/\.](0?[1-9]|1[0-2])[-/\.](20\d{2}|19\d{2})\b"
    r"|"
    r"\b(0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])[-/\.](20\d{2}|19\d{2})\b",
    re.IGNORECASE,
)

def parse_fields(text: str) -> Dict:
    amounts = [float(m.replace(",", "")) for m in re.findall(r"\d{1,3}(?:,\d{3})*\.\d{2}", text)]
    total = max(amounts) if amounts else None

    vendor = None
    banned = {"total", "subtotal", "tax", "invoice", "receipt", "amount", "cashier", "date"}
    for ln in [l.strip() for l in text.splitlines() if l.strip()][:15]:
        clean = re.sub(r"[^A-Za-z0-9 &\-\.\,]", "", ln)
        if len(clean) >= 3 and not any(w in clean.lower() for w in banned):
            vendor = clean[:60]; break

    m = _DATE_PAT.search(text.replace(" ", ""))
    invoice_date = m.group(0) if m else None

    inv = re.search(r"(invoice|inv|bill)\s*(no\.?|#|num(?:ber)?)?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
                    text, re.IGNORECASE)
    invoice_no = inv.group(3) if inv else None

    return {"vendor": vendor, "invoice_date": invoice_date, "invoice_number": invoice_no, "total_amount": total}
