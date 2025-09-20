#!/usr/bin/env python3
"""
Simple test script to debug OCR issues
"""
import os
from backend.utils.ocr_paddle import ocr_image

def test_ocr_with_sample():
    """Test OCR with a sample image file"""
    
    # Check if there's a sample image in the project
    sample_paths = [
        "sample.jpg", "sample.png", "test.jpg", "test.png",
        "receipt.jpg", "receipt.png", "invoice.jpg", "invoice.png"
    ]
    
    sample_file = None
    for path in sample_paths:
        if os.path.exists(path):
            sample_file = path
            break
    
    if not sample_file:
        print("No sample image found. Please add a test image (sample.jpg/png) to test OCR.")
        print("You can also manually test by providing an image path.")
        return
    
    print(f"Testing OCR with: {sample_file}")
    
    try:
        with open(sample_file, 'rb') as f:
            file_bytes = f.read()
        
        print("Running OCR...")
        result = ocr_image(file_bytes)
        
        print("\n=== OCR RESULTS ===")
        print(f"Engine: {result['engine']}")
        print(f"Pages: {result['pages']}")
        print(f"Text detected: {len(result['text'])} characters")
        print(f"Approx total: {result['approx_total']}")
        print(f"Debug saved: {result['debug_saved']}")
        
        if result['text']:
            print("\n=== EXTRACTED TEXT ===")
            print(result['text'])
        else:
            print("\n!!! NO TEXT DETECTED !!!")
            print("Check debug images in:", result['debug_dir'])
            
    except Exception as e:
        print(f"Error during OCR: {e}")
        import traceback
        traceback.print_exc()

def test_ocr_with_custom_file(file_path):
    """Test OCR with a specific file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    print(f"Testing OCR with: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        print("Running OCR...")
        result = ocr_image(file_bytes)
        
        print("\n=== OCR RESULTS ===")
        print(f"Engine: {result['engine']}")
        print(f"Pages: {result['pages']}")
        print(f"Text detected: {len(result['text'])} characters")
        print(f"Approx total: {result['approx_total']}")
        
        if result['text']:
            print("\n=== EXTRACTED TEXT ===")
            print(result['text'])
        else:
            print("\n!!! NO TEXT DETECTED !!!")
            if result['debug_saved']:
                print("Check debug images in:", result['debug_dir'])
            
    except Exception as e:
        print(f"Error during OCR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test with provided file path
        test_ocr_with_custom_file(sys.argv[1])
    else:
        # Test with sample file
        test_ocr_with_sample()