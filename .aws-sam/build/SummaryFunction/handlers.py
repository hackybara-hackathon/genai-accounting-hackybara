import json
import boto3
import base64
import uuid
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics

# Import our modules
from db import (
    get_db_cursor, upsert_vendor, get_or_create_category, insert_document,
    insert_ocr_result, insert_transaction, get_transactions_with_filters,
    get_summary_data, get_monthly_report, get_forecast_data, save_forecast,
    get_latest_forecast
)
from parsers import parse_fields, normalize_date, extract_currency, clean_text_for_db, validate_amount
from bedrock_client import bedrock_client, keyword_guess

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')

# Environment variables
ORG_ID = os.environ['ORG_ID']
BUCKET_NAME = os.environ['BUCKET_NAME']

def upload_to_s3(file_b64: str, filename: str) -> str:
    """Upload base64 file to S3 and return S3 key"""
    try:
        # Decode base64 file
        file_data = base64.b64decode(file_b64)
        
        # Generate unique S3 key
        file_id = str(uuid.uuid4())
        s3_key = f"receipts/{file_id}/{filename}"
        
        # Determine content type
        content_type = get_content_type(filename)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_data,
            ContentType=content_type
        )
        
        logger.info(f"Uploaded file to S3: {s3_key}")
        return s3_key
        
    except Exception as e:
        logger.error(f"S3 upload failed: {str(e)}")
        raise

def get_content_type(filename: str) -> str:
    """Get content type based on file extension"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'pdf': 'application/pdf',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'tiff': 'image/tiff'
    }
    return content_types.get(ext, 'application/octet-stream')

def get_s3_url(s3_key: str) -> str:
    """Generate S3 URL for a key"""
    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

def lambda_response(status_code: int, body: Dict, headers: Optional[Dict] = None) -> Dict:
    """Standard Lambda response format"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=str)
    }

def classify_handler(event, context):
    """POST /classify - Process receipt upload and classification"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Org ID: {ORG_ID}")
    
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
            return lambda_response(400, {'error': 'file_base64 is required'})
        
        # Upload file to S3
        s3_key = upload_to_s3(file_base64, filename)
        document_url = get_s3_url(s3_key)
        
        # Parse fields from OCR text
        parsed_fields = parse_fields(ocr_text)
        vendor_name = parsed_fields.get('vendor', 'Unknown Vendor')
        total_amount = validate_amount(parsed_fields.get('total_amount', 0))
        invoice_date = normalize_date(parsed_fields.get('invoice_date'))
        invoice_number = parsed_fields.get('invoice_number')
        currency = extract_currency(ocr_text)
        
        # Classify using Bedrock or fallback to keywords
        category_name = bedrock_client.classify_receipt(ocr_text) or keyword_guess(ocr_text)
        
        # Database operations in transaction
        with get_db_cursor() as cur:
            # Insert document
            document_id = insert_document(
                cur, ORG_ID, filename, document_url, 'receipt'
            )
            
            # Upsert vendor
            vendor_id = upsert_vendor(cur, ORG_ID, vendor_name) if vendor_name != 'Unknown Vendor' else None
            
            # Insert OCR result
            ocr_result_id = insert_ocr_result(
                cur, ORG_ID, document_id, vendor_id, 
                clean_text_for_db(ocr_text), total_amount, currency,
                invoice_date, invoice_number
            )
            
            # Get or create category
            category_id = get_or_create_category(cur, ORG_ID, category_name)
            
            # Insert transaction
            transaction_id = insert_transaction(
                cur, ORG_ID, document_id, ocr_result_id, vendor_id, 
                None, category_id, vendor_name, total_amount, currency, 
                invoice_date, 'expense'
            )
        
        logger.info(f"Successfully processed receipt: {document_id}, transaction: {transaction_id}")
        
        # Return response
        response_data = {
            'document_id': document_id,
            'ocr_result_id': ocr_result_id,
            'transaction_id': transaction_id,
            'vendor': vendor_name,
            'invoice_date': invoice_date,
            'total_amount': total_amount,
            'currency': currency,
            'category': category_name,
            's3_key': s3_key
        }
        
        return lambda_response(200, response_data)
        
    except Exception as e:
        logger.error(f"Classify handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def transactions_handler(event, context):
    """GET /transactions - List transactions with filters"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Org ID: {ORG_ID}")
    
    try:
        # Parse query parameters
        params = event.get('queryStringParameters') or {}
        
        limit = int(params.get('limit', 50))
        offset = int(params.get('offset', 0))
        from_date = params.get('from')
        to_date = params.get('to')
        category = params.get('category')
        vendor = params.get('vendor')
        
        # Validate and clamp limit
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        
        # Normalize dates
        if from_date:
            from_date = normalize_date(from_date)
        if to_date:
            to_date = normalize_date(to_date)
        
        with get_db_cursor() as cur:
            items, total = get_transactions_with_filters(
                cur, ORG_ID, limit, offset, from_date, to_date, category, vendor
            )
        
        logger.info(f"Retrieved {len(items)} transactions (total: {total})")
        
        return lambda_response(200, {
            'items': items,
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Transactions handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def summary_handler(event, context):
    """GET /summary - Get KPIs and spending summary"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Org ID: {ORG_ID}")
    
    try:
        with get_db_cursor() as cur:
            summary_data = get_summary_data(cur, ORG_ID)
        
        logger.info(f"Generated summary with {len(summary_data['by_category_90d'])} categories")
        
        return lambda_response(200, summary_data)
        
    except Exception as e:
        logger.error(f"Summary handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def report_monthly_handler(event, context):
    """GET /report/monthly - Get monthly report by category"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Org ID: {ORG_ID}")
    
    try:
        # Parse query parameters
        params = event.get('queryStringParameters') or {}
        year = int(params.get('year', datetime.now().year))
        
        # Validate year
        if year < 2020 or year > 2030:
            return lambda_response(400, {'error': 'Invalid year'})
        
        with get_db_cursor() as cur:
            report_data = get_monthly_report(cur, ORG_ID, year)
        
        logger.info(f"Generated monthly report for {year} with {len(report_data)} entries")
        
        return lambda_response(200, report_data)
        
    except Exception as e:
        logger.error(f"Monthly report handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def forecast_handler(event, context):
    """GET /forecast - Generate or retrieve cash flow forecast"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Org ID: {ORG_ID}")
    
    try:
        with get_db_cursor() as cur:
            # Check for existing recent forecast
            existing_forecast = get_latest_forecast(cur, ORG_ID, max_age_hours=24)
            
            if existing_forecast:
                logger.info("Using cached forecast")
                return lambda_response(200, existing_forecast)
            
            # Generate new forecast
            historical_data = get_forecast_data(cur, ORG_ID)
            
            if len(historical_data) < 4:  # Need at least 4 weeks of data
                return lambda_response(200, {
                    'series': [],
                    'message': 'Insufficient data for forecasting (minimum 4 weeks required)'
                })
            
            # Apply simple forecasting algorithm
            forecast_series = generate_forecast(historical_data)
            
            # Save forecast to database
            save_forecast(cur, ORG_ID, horizon=8, granularity='week', series=forecast_series)
        
        logger.info(f"Generated forecast with {len(forecast_series)} data points")
        
        return lambda_response(200, {'series': forecast_series})
        
    except Exception as e:
        logger.error(f"Forecast handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def insights_handler(event, context):
    """POST /insights - Generate AI-powered business insights"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Org ID: {ORG_ID}")
    
    try:
        # Parse optional question from request
        question = None
        if event.get('body'):
            try:
                body = json.loads(event['body'])
                question = body.get('question')
            except json.JSONDecodeError:
                pass
        
        # Gather context data
        with get_db_cursor() as cur:
            # Get summary data
            summary_data = get_summary_data(cur, ORG_ID)
            
            # Get top vendors (last 90 days)
            cur.execute("""
                SELECT v.name, SUM(t.amount) as total
                FROM transactions t
                LEFT JOIN vendors v ON v.id = t.vendor_id
                WHERE t.organization_id = %s 
                    AND t.type = 'expense'
                    AND COALESCE(t.invoice_date, t.created_at::date) >= CURRENT_DATE - INTERVAL '90 days'
                    AND v.name IS NOT NULL
                GROUP BY v.name
                ORDER BY total DESC
                LIMIT 5
            """, (ORG_ID,))
            
            top_vendors = []
            for row in cur.fetchall():
                top_vendors.append({
                    'vendor': row['name'],
                    'total': float(row['total']) if row['total'] else 0.0
                })
            
            # Get recent forecast data
            forecast_data = get_forecast_data(cur, ORG_ID)
            recent_forecast = forecast_data[-4:] if len(forecast_data) >= 4 else forecast_data
        
        # Prepare context for AI
        context_data = {
            'kpis': summary_data['kpis'],
            'spending_by_category_90d': summary_data['by_category_90d'],
            'top_vendors_90d': top_vendors,
            'recent_cash_flow': recent_forecast,
            'question': question
        }
        
        # Generate insights using Bedrock
        insights = bedrock_client.generate_insights(context_data)
        
        logger.info("Generated business insights")
        
        return lambda_response(200, insights)
        
    except Exception as e:
        logger.error(f"Insights handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def generate_forecast(historical_data: List[Dict]) -> List[Dict]:
    """
    Simple forecasting using moving average with trend adjustment
    """
    if len(historical_data) < 4:
        return []
    
    # Extract net cash flow values
    net_values = [item['net'] for item in historical_data]
    
    # Calculate moving averages for trend
    window_size = min(4, len(net_values))
    moving_averages = []
    
    for i in range(len(net_values) - window_size + 1):
        avg = statistics.mean(net_values[i:i + window_size])
        moving_averages.append(avg)
    
    # Calculate trend (slope of recent moving averages)
    if len(moving_averages) >= 2:
        recent_avg = statistics.mean(moving_averages[-2:])
        older_avg = statistics.mean(moving_averages[:2])
        trend = (recent_avg - older_avg) / len(moving_averages)
    else:
        trend = 0
    
    # Generate forecast for next 8 weeks
    last_date = datetime.fromisoformat(historical_data[-1]['week'])
    forecast_series = []
    
    # Add historical data to series
    for item in historical_data:
        forecast_series.append({
            'week': item['week'],
            'net': item['net'],
            'forecast': None,  # No forecast for historical data
            'is_forecast': False
        })
    
    # Generate forecasts
    base_value = statistics.mean(net_values[-window_size:])  # Average of recent values
    
    for i in range(8):  # Forecast 8 weeks ahead
        forecast_date = last_date + timedelta(weeks=i + 1)
        
        # Simple trend-adjusted forecast with some dampening
        dampening_factor = 0.9 ** i  # Reduce trend impact over time
        forecast_value = base_value + (trend * (i + 1) * dampening_factor)
        
        forecast_series.append({
            'week': forecast_date.isoformat(),
            'net': None,  # No actual data for future
            'forecast': round(forecast_value, 2),
            'is_forecast': True
        })
    
    return forecast_series