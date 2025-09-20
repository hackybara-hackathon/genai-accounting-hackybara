import json
import boto3
import base64
import uuid
import datetime
import logging
import re
import os
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock_client = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'ap-southeast-1'))

# Environment variables
TABLE_NAME = os.environ['TABLE_NAME']
BUCKET_NAME = os.environ['BUCKET_NAME']
MODEL_ID = os.environ['MODEL_ID']

# DynamoDB table
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Main Lambda handler for receipt processing
    """
    try:
        # Parse request body
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body']).decode('utf-8')
        else:
            body = event['body']
        
        request_data = json.loads(body)
        
        # Extract required fields
        file_base64 = request_data.get('file_base64', '')
        filename = request_data.get('filename', 'receipt.jpg')
        ocr_text = request_data.get('ocr_text', '')
        
        if not file_base64:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'file_base64 is required'})
            }
        
        # Generate unique receipt ID
        receipt_id = str(uuid.uuid4())
        s3_key = f"receipts/{receipt_id}/{filename}"
        
        logger.info(f"Processing receipt {receipt_id}, s3_key: {s3_key}")
        
        # Upload file to S3
        file_data = base64.b64decode(file_base64)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_data,
            ContentType=get_content_type(filename)
        )
        
        # Parse fields from OCR text
        parsed_fields = parse_fields(ocr_text)
        
        # Categorize using Bedrock or fallback to keywords
        category = bedrock_classify(ocr_text) or keyword_guess(ocr_text)
        
        # Create receipt record
        receipt_record = {
            'receipt_id': receipt_id,
            'vendor': parsed_fields.get('vendor', ''),
            'invoice_date': parsed_fields.get('invoice_date', ''),
            'invoice_number': parsed_fields.get('invoice_number', ''),
            'total_amount': Decimal(str(parsed_fields.get('total_amount', 0))),
            'category': category,
            'raw_text': (ocr_text[:3500] if ocr_text else ''),
            's3_key': s3_key,
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        
        # Save to DynamoDB
        table.put_item(Item=receipt_record)
        
        # Convert Decimal to float for JSON response
        response_record = json.loads(json.dumps(receipt_record, default=decimal_default))
        
        logger.info(f"Successfully processed receipt {receipt_id}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_record)
        }
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def parse_fields(text):
    """
    Parse vendor, invoice_date, invoice_number, total_amount from OCR text
    """
    fields = {
        'vendor': None,
        'invoice_date': None,
        'invoice_number': None,
        'total_amount': 0
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
        r'\b(20\d{2}|19\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])\b',  # YYYY-MM-DD
        r'\b(0?[1-9]|[12]\d|3[01])[-/\.](0?[1-9]|1[0-2])[-/\.](20\d{2}|19\d{2})\b',  # DD/MM/YYYY
        r'\b(0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])[-/\.](20\d{2}|19\d{2})\b'   # MM/DD/YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text.replace(' ', ''))
        if match:
            fields['invoice_date'] = match.group(0)
            break
    
    # Parse invoice_number
    invoice_patterns = [
        r'(invoice|inv|bill)\s*(no\.?|#|num(?:ber)?)?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)',
        r'receipt\s*(no\.?|#)?\s*[:\-]?\s*([A-Za-z0-9\-\/]+)'
    ]
    
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields['invoice_number'] = match.group(-1)  # Last group
            break
    
    # Parse vendor - first non-keyword line near the top
    banned_keywords = {'total', 'subtotal', 'tax', 'invoice', 'receipt', 'amount', 'cashier', 'date', 'time'}
    lines = [line.strip() for line in text.splitlines() if line.strip()][:15]
    
    for line in lines:
        clean_line = re.sub(r'[^A-Za-z0-9 &\-\.\,]', '', line)
        if (len(clean_line) >= 3 and len(clean_line) <= 60 and 
            not any(keyword in clean_line.lower() for keyword in banned_keywords)):
            fields['vendor'] = clean_line
            break
    
    return fields

def bedrock_classify(text):
    """
    Classify receipt using Amazon Bedrock
    """
    if not text:
        return None
    
    try:
        prompt = f"""You are a strict receipt categorizer for SMEs.
Return ONLY a JSON object with a single key "category".
The value MUST be one of: ["Food & Beverage","Utilities","Transportation","Office Supplies","Others"].
If unsure, choose "Others".
Receipt text:
{text[:2000]}
JSON:"""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', content)
        if json_match:
            result = json.loads(json_match.group())
            category = result.get('category')
            
            # Validate category
            valid_categories = ["Food & Beverage", "Utilities", "Transportation", "Office Supplies", "Others"]
            if category in valid_categories:
                logger.info(f"Bedrock classified as: {category}")
                return category
        
        logger.warning("Bedrock returned invalid category format")
        return None
        
    except Exception as e:
        logger.error(f"Bedrock classification failed: {str(e)}")
        return None

def keyword_guess(text):
    """
    Fallback keyword-based classification
    """
    if not text:
        return "Others"
    
    text_lower = text.lower()
    
    # Category keyword mappings
    category_keywords = {
        "Food & Beverage": [
            'kfc', 'mcdonald', 'burger king', 'pizza', 'starbucks', 'coffee', 'restaurant',
            'cafe', 'food', 'meal', 'lunch', 'dinner', 'breakfast', 'drink', 'beverages',
            'bar', 'pub', 'bakery', 'grocery', 'supermarket', 'market'
        ],
        "Utilities": [
            'electric', 'electricity', 'water', 'gas', 'internet', 'phone', 'mobile',
            'utility', 'bill', 'telecommunications', 'broadband', 'wifi', 'power',
            'energy', 'heating', 'cooling'
        ],
        "Transportation": [
            'taxi', 'uber', 'grab', 'bus', 'train', 'mrt', 'lrt', 'fuel', 'petrol',
            'gasoline', 'parking', 'toll', 'highway', 'transport', 'flight', 'airline',
            'car', 'vehicle', 'motorcycle', 'bike'
        ],
        "Office Supplies": [
            'office', 'stationery', 'paper', 'pen', 'pencil', 'printer', 'ink',
            'cartridge', 'supplies', 'equipment', 'computer', 'laptop', 'software',
            'hardware', 'furniture', 'desk', 'chair'
        ]
    }
    
    # Count matches for each category
    category_scores = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            category_scores[category] = score
    
    # Return category with highest score, or "Others" if no matches
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        logger.info(f"Keyword classification: {best_category} (score: {category_scores[best_category]})")
        return best_category
    
    return "Others"

def get_content_type(filename):
    """
    Get content type based on file extension
    """
    ext = filename.lower().split('.')[-1]
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'pdf': 'application/pdf'
    }
    return content_types.get(ext, 'application/octet-stream')

def decimal_default(obj):
    """
    JSON serializer for Decimal objects
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError