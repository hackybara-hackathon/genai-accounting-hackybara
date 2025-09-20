# backend/app.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.utils.ocr_paddle import ocr_image, parse_fields

app = FastAPI(title="GenAI Accounting - OCR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    data = await file.read()
    result = ocr_image(data)
    return JSONResponse(result)

@app.post("/ocr/parse")
async def ocr_parse_endpoint(file: UploadFile = File(...)):
    data = await file.read()
    result = ocr_image(data)
    fields = parse_fields(result["text"])
    result["fields"] = fields
    return JSONResponse(result)
