#!/usr/bin/env python3
"""
Create a simple test image with text for OCR testing
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    """Create a simple test image with text"""
    
    # Create a white image
    width, height = 800, 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a system font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
        except:
            font = ImageFont.load_default()
    
    # Add some text
    text_lines = [
        "INVOICE",
        "Company ABC Inc.",
        "Date: 2024-01-15",
        "Invoice #: INV-001",
        "Total: $124.50"
    ]
    
    y_position = 50
    for line in text_lines:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 80
    
    # Save the image
    image.save('test_receipt.png')
    print("Test image created: test_receipt.png")
    return 'test_receipt.png'

if __name__ == "__main__":
    create_test_image()