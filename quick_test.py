#!/usr/bin/env python3
"""
Quick OCR test
"""
from backend.utils.ocr_paddle import ocr_image

def quick_test():
    try:
        with open('test_receipt.png', 'rb') as f:
            file_bytes = f.read()
        
        result = ocr_image(file_bytes)
        
        print("=== QUICK TEST RESULTS ===")
        print(f"Text length: {len(result['text'])}")
        print(f"Text: {result['text']}")
        print(f"Total: {result['approx_total']}")
        
        if result['text']:
            print("✅ OCR is working correctly!")
        else:
            print("❌ OCR still not detecting text")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()