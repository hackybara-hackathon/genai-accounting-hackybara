import re
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger()

def parse_fields(text: str) -> Dict[str, any]:
    """
    Parse vendor, invoice_date, invoice_number, total_amount from OCR text
    """
    fields = {
        'vendor': None,
        'invoice_date': None,
        'invoice_number': None,
        'total_amount': 0.0
    }
    
    if not text:
        return fields
    
    # Parse total_amount - highest number matching pattern
    amounts = []
    amount_pattern = r'\d{1,3}(?:,\d{3})*\.\d{2}'
    for match in re.finditer(amount_pattern, text):
        try:
            amount = float(match.group().replace(',', ''))
            amounts.append(amount)
        except ValueError:
            continue
    
    if amounts:
        fields['total_amount'] = max(amounts)
    
    # Parse invoice_date - support multiple formats
    date_patterns = [
        (r'\b(20\d{2}|19\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])\b', '%Y-%m-%d'),  # YYYY-MM-DD
        (r'\b(0?[1-9]|[12]\d|3[01])[-/\.](0?[1-9]|1[0-2])[-/\.](20\d{2}|19\d{2})\b', '%d-%m-%Y'),  # DD/MM/YYYY
        (r'\b(0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])[-/\.](20\d{2}|19\d{2})\b', '%m-%d-%Y')   # MM/DD/YYYY
    ]
    
    for pattern, format_hint in date_patterns:
        match = re.search(pattern, text.replace(' ', ''))
        if match:
            try:
                date_str = match.group(0)
                # Normalize separators to -
                normalized_date = re.sub(r'[/\.]', '-', date_str)
                
                # Try to parse with different formats
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y']:
                    try:
                        parsed_date = datetime.strptime(normalized_date, fmt)
                        fields['invoice_date'] = parsed_date.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
                
                if fields['invoice_date']:
                    break
            except Exception as e:
                logger.warning(f"Date parsing error: {e}")
                continue
    
    # Parse invoice_number
    invoice_patterns = [
        r'(?:invoice|inv|bill)\s*(?:no\.?|#|num(?:ber)?)?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)',
        r'receipt\s*(?:no\.?|#)?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)',
        r'ref(?:erence)?\s*(?:no\.?|#)?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)'
    ]
    
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and len(match.group(1).strip()) >= 3:
            fields['invoice_number'] = match.group(1).strip()
            break
    
    # Parse vendor - first non-keyword line near the top
    banned_keywords = {
        'total', 'subtotal', 'tax', 'invoice', 'receipt', 'amount', 'cashier', 
        'date', 'time', 'thank', 'you', 'welcome', 'payment', 'change', 'balance',
        'gst', 'vat', 'service', 'charge', 'www', 'http', 'email', 'phone', 'tel'
    }
    
    lines = [line.strip() for line in text.splitlines() if line.strip()][:15]
    
    for line in lines:
        # Clean the line - remove special characters but keep alphanumeric, spaces, &, -, ., ,
        clean_line = re.sub(r'[^A-Za-z0-9 &\-\.\,]', '', line)
        clean_line = clean_line.strip()
        
        # Skip if too short, too long, or contains banned keywords
        if (len(clean_line) < 3 or len(clean_line) > 60 or
            any(keyword in clean_line.lower() for keyword in banned_keywords)):
            continue
        
        # Skip if it's mostly numbers or looks like an address/phone
        if (re.search(r'^\d+[\d\s\-]*$', clean_line) or  # Mostly numbers
            re.search(r'\d{3,}[-\s]\d{3,}', clean_line) or  # Phone-like
            len(re.findall(r'\d', clean_line)) > len(clean_line) / 2):  # More than 50% digits
            continue
        
        fields['vendor'] = clean_line
        break
    
    return fields

def normalize_date(date_str: str) -> Optional[str]:
    """
    Normalize date string to YYYY-MM-DD format
    """
    if not date_str:
        return None
    
    # Try various date formats
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%m-%d-%Y',
        '%Y/%m/%d',
        '%d.%m.%Y',
        '%m.%d.%Y'
    ]
    
    # Clean the date string
    clean_date = re.sub(r'[^\d/\-\.]', '', date_str)
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(clean_date, fmt)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None

def extract_currency(text: str) -> str:
    """
    Extract currency from text, default to MYR
    """
    if not text:
        return "MYR"
    
    # Common currency patterns
    currency_patterns = [
        (r'\bUSD\b|\$(?!\d)', 'USD'),
        (r'\bEUR\b|€', 'EUR'),
        (r'\bGBP\b|£', 'GBP'),
        (r'\bSGD\b|S\$', 'SGD'),
        (r'\bMYR\b|RM\b', 'MYR'),
        (r'\bTHB\b|฿', 'THB'),
        (r'\bINR\b|₹', 'INR'),
        (r'\bJPY\b|¥', 'JPY')
    ]
    
    text_upper = text.upper()
    for pattern, currency in currency_patterns:
        if re.search(pattern, text_upper):
            return currency
    
    # Default to MYR for SEA region
    return "MYR"

def clean_text_for_db(text: str, max_length: int = 3500) -> str:
    """
    Clean and truncate text for database storage
    """
    if not text:
        return ""
    
    # Remove null bytes and other problematic characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)
    
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned

def validate_amount(amount: any) -> float:
    """
    Validate and clean amount value
    """
    if amount is None:
        return 0.0
    
    try:
        if isinstance(amount, str):
            # Remove currency symbols and commas
            clean_amount = re.sub(r'[^\d\.-]', '', amount)
            return float(clean_amount) if clean_amount else 0.0
        return float(amount)
    except (ValueError, TypeError):
        return 0.0

def extract_vendor_keywords(text: str) -> List[str]:
    """
    Extract potential vendor keywords for classification
    """
    if not text:
        return []
    
    # Extract meaningful words (excluding common receipt terms)
    words = re.findall(r'\b[A-Za-z]{3,}\b', text.upper())
    
    # Filter out common receipt words
    common_words = {
        'RECEIPT', 'INVOICE', 'BILL', 'TOTAL', 'SUBTOTAL', 'TAX', 'GST', 'VAT',
        'PAYMENT', 'CASH', 'CARD', 'CREDIT', 'DEBIT', 'CHANGE', 'BALANCE',
        'DATE', 'TIME', 'CASHIER', 'THANK', 'YOU', 'WELCOME', 'CUSTOMER',
        'SERVICE', 'CHARGE', 'AMOUNT', 'QTY', 'QUANTITY', 'PRICE', 'ITEM'
    }
    
    keywords = [word for word in words if word not in common_words and len(word) >= 3]
    
    # Return first 10 unique keywords
    return list(dict.fromkeys(keywords))[:10]