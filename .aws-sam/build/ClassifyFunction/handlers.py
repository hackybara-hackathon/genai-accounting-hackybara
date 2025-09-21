import json
import boto3
import base64
import uuid
import os
import logging
import hashlib
import jwt
import bcrypt
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

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    try:
        import bcrypt
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except ImportError:
        # Fallback to simple hashing if bcrypt not available
        logger.warning("bcrypt not available, using simple hash")
        return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ImportError:
        # Fallback for simple hash
        return hashlib.sha256(password.encode()).hexdigest() == hashed

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
    """Standard Lambda response format with CORS headers"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=str)
    }

def options_handler(event, context):
    """Handle OPTIONS requests for CORS preflight"""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,PUT,DELETE',
            'Access-Control-Max-Age': '86400'
        },
        'body': ''
    }

def cors_handler(func):
    """Decorator to ensure CORS headers are always returned"""
    def wrapper(event, context):
        try:
            return func(event, context)
        except Exception as e:
            logger.error(f"Handler {func.__name__} error: {str(e)}", exc_info=True)
            return lambda_response(500, {'error': 'Internal server error'})
    return wrapper

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
        filename = request_data.get('filename', 'receipt.txt')
        ocr_text = request_data.get('ocr_text', '')
        user_id = request_data.get('user_id', '')
        org_id = request_data.get('organization_id', ORG_ID)  # Use provided org_id or fallback to env var
        
        # Require either file_base64 or ocr_text
        if not file_base64 and not ocr_text:
            return lambda_response(400, {'error': 'Either file_base64 or ocr_text is required'})
        
        # Require user_id for proper document ownership
        if not user_id:
            return lambda_response(400, {'error': 'user_id is required'})
        
        # Upload file to S3 if file_base64 is provided
        document_url = None
        if file_base64:
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
            # Insert document with the authenticated user_id
            document_id = insert_document(
                cur, org_id, filename, document_url, 'receipt', user_id
            )
            
            # Upsert vendor
            vendor_id = upsert_vendor(cur, org_id, vendor_name) if vendor_name != 'Unknown Vendor' else None
            
            # Insert OCR result
            ocr_result_id = insert_ocr_result(
                cur, org_id, document_id, vendor_id, 
                clean_text_for_db(ocr_text), total_amount, currency,
                invoice_date, invoice_number, user_id
            )
            
            # Get or create category
            category_id = get_or_create_category(cur, org_id, category_name)
            
            # Insert transaction
            transaction_id = insert_transaction(
                cur, org_id, ocr_result_id, vendor_id, 
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

def tax_advisor_handler(event, context):
    """POST /ai/tax-advisor - AI Tax Preparation Assistant"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Tax Advisor Query")
    
    try:
        # Parse request body
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body']).decode('utf-8')
        else:
            body = event['body']
        
        request_data = json.loads(body)
        user_query = request_data.get('query', '')
        
        if not user_query:
            return lambda_response(400, {'error': 'Query is required'})
        
        # Get user's financial context
        transaction_data = None
        with get_db_cursor() as cur:
            try:
                summary_data = get_summary_data(cur, ORG_ID)
                transaction_data = {
                    'total_expenses': summary_data['kpis']['total_spent_90d'],
                    'business_expenses': sum(cat['amount'] for cat in summary_data['by_category_90d'] 
                                           if cat['category'] in ['Business Expenses', 'Office Supplies', 'Professional Services']),
                    'receipt_count': summary_data['kpis']['documents_90d'],
                    'top_categories': [cat['category'] for cat in summary_data['by_category_90d'][:5]]
                }
            except Exception as e:
                logger.warning(f"Could not get transaction data: {str(e)}")
        
        # Get AI advice
        advice = bedrock_client.tax_preparation_advisor(user_query, transaction_data)
        
        return lambda_response(200, {
            'query': user_query,
            'advice': advice,
            'context_included': transaction_data is not None
        })
        
    except Exception as e:
        logger.error(f"Tax advisor handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def financial_advisor_handler(event, context):
    """POST /ai/financial-advisor - AI Financial Planning Assistant"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Financial Advisor Query")
    
    try:
        # Parse request body
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body']).decode('utf-8')
        else:
            body = event['body']
        
        request_data = json.loads(body)
        user_query = request_data.get('query', '')
        
        if not user_query:
            return lambda_response(400, {'error': 'Query is required'})
        
        # Get user's financial summary
        financial_summary = None
        with get_db_cursor() as cur:
            try:
                summary_data = get_summary_data(cur, ORG_ID)
                
                # Calculate monthly average
                monthly_avg = summary_data['kpis']['total_spent_90d'] / 3  # 90 days = ~3 months
                
                # Get trend from recent vs older spending
                cur.execute("""
                    SELECT 
                        SUM(CASE WHEN COALESCE(invoice_date, created_at::date) >= CURRENT_DATE - INTERVAL '30 days' THEN amount ELSE 0 END) as recent_30d,
                        SUM(CASE WHEN COALESCE(invoice_date, created_at::date) BETWEEN CURRENT_DATE - INTERVAL '60 days' AND CURRENT_DATE - INTERVAL '30 days' THEN amount ELSE 0 END) as previous_30d
                    FROM transactions 
                    WHERE organization_id = %s AND type = 'expense'
                """, (ORG_ID,))
                
                trend_data = cur.fetchone()
                recent_30d = float(trend_data['recent_30d']) if trend_data['recent_30d'] else 0
                previous_30d = float(trend_data['previous_30d']) if trend_data['previous_30d'] else 0
                
                if previous_30d > 0:
                    trend = "Increasing" if recent_30d > previous_30d else "Decreasing" if recent_30d < previous_30d else "Stable"
                else:
                    trend = "Unknown"
                
                financial_summary = {
                    'monthly_avg': monthly_avg,
                    'trend': trend,
                    'top_categories': [cat['category'] for cat in summary_data['by_category_90d'][:3]],
                    'variance': 'High' if abs(recent_30d - previous_30d) > previous_30d * 0.2 else 'Stable',
                    'recent_count': summary_data['kpis']['documents_30d']
                }
            except Exception as e:
                logger.warning(f"Could not get financial summary: {str(e)}")
        
        # Get AI advice
        advice = bedrock_client.financial_advisor(user_query, financial_summary)
        
        return lambda_response(200, {
            'query': user_query,
            'advice': advice,
            'financial_context': financial_summary
        })
        
    except Exception as e:
        logger.error(f"Financial advisor handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def budget_recommendations_handler(event, context):
    """POST /ai/budget-recommendations - AI Budget Planning Assistant"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Budget Recommendations Query")
    
    try:
        # Parse request body
        request_data = {}
        if event.get('body'):
            try:
                if event.get('isBase64Encoded', False):
                    body = base64.b64decode(event['body']).decode('utf-8')
                else:
                    body = event['body']
                request_data = json.loads(body)
            except json.JSONDecodeError:
                pass
        
        user_goals = request_data.get('goals', '')
        
        # Get spending data
        with get_db_cursor() as cur:
            summary_data = get_summary_data(cur, ORG_ID)
            
            # Calculate monthly trend
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN COALESCE(invoice_date, created_at::date) >= CURRENT_DATE - INTERVAL '30 days' THEN amount ELSE 0 END) as recent_30d,
                    SUM(CASE WHEN COALESCE(invoice_date, created_at::date) BETWEEN CURRENT_DATE - INTERVAL '60 days' AND CURRENT_DATE - INTERVAL '30 days' THEN amount ELSE 0 END) as previous_30d
                FROM transactions 
                WHERE organization_id = %s AND type = 'expense'
            """, (ORG_ID,))
            
            trend_data = cur.fetchone()
            recent_30d = float(trend_data['recent_30d']) if trend_data['recent_30d'] else 0
            previous_30d = float(trend_data['previous_30d']) if trend_data['previous_30d'] else 0
            
            if previous_30d > 0:
                trend = "increasing" if recent_30d > previous_30d else "decreasing" if recent_30d < previous_30d else "stable"
            else:
                trend = "stable"
            
            # Prepare spending data
            categories = {}
            for cat in summary_data['by_category_90d']:
                categories[cat['category']] = cat['amount'] / 3  # Convert to monthly average
            
            spending_data = {
                'total_spending': sum(categories.values()),
                'categories': categories,
                'monthly_trend': trend
            }
        
        # Get AI recommendations
        recommendations = bedrock_client.budget_recommendations(spending_data, user_goals)
        
        return lambda_response(200, {
            'recommendations': recommendations,
            'current_spending': spending_data,
            'goals': user_goals
        })
        
    except Exception as e:
        logger.error(f"Budget recommendations handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def ai_chat_handler(event, context):
    """POST /ai/chat - Unified AI Assistant for all accounting and finance tasks"""
    request_id = context.aws_request_id
    logger.info(f"Request ID: {request_id}, Unified AI Chat Query")
    
    try:
        # Parse request body
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body']).decode('utf-8')
        else:
            body = event['body']
        
        request_data = json.loads(body)
        user_message = request_data.get('message', '')
        conversation_context = request_data.get('context', [])
        
        if not user_message:
            return lambda_response(400, {'error': 'Message is required'})
        
        # Limit conversation context to prevent token overflow
        if len(conversation_context) > 5:
            conversation_context = conversation_context[-5:]
        
        # Use simple direct AI call instead of specialized methods
        response = get_unified_ai_response(user_message, conversation_context)
        
        return lambda_response(200, {
            'message': user_message,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"AI chat handler error: {str(e)}", exc_info=True)
        return lambda_response(500, {'error': 'Internal server error'})

def get_unified_ai_response(user_message: str, conversation_context: List[Dict] = None) -> str:
    """
    Simple unified AI function that handles all accounting and finance tasks
    """
    # Build conversation context
    context_text = ""
    if conversation_context:
        context_text = "Previous conversation:\n"
        for msg in conversation_context[-3:]:  # Last 3 messages
            role = msg.get('role', 'user')
            content = msg.get('content', msg.get('message', ''))
            context_text += f"{role}: {content}\n"
        context_text += "\n"
    
    # Create a comprehensive prompt for accounting assistant
    prompt = f"""You are Hackybara AI, an expert accounting and finance assistant for small and medium businesses. You help with:

• Financial reports and analysis
• Expense categorization and tracking  
• Cash flow predictions and trends
• Tax preparation and planning
• Budget recommendations and planning
• General accounting questions
• Business financial insights

{context_text}User: {user_message}

Please provide helpful, accurate, and actionable advice. Keep responses practical and business-focused. If you need more specific information to give better advice, ask clarifying questions.
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

# ===============================
# AUTHENTICATION HANDLERS
# ===============================

def login_handler(event, context):
    """POST /login - User authentication"""
    try:
        # Parse request body
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body']).decode('utf-8')
        else:
            body = event['body']
        
        request_data = json.loads(body)
        email = request_data.get('email', '').strip().lower()
        password = request_data.get('password', '')
        
        if not email or not password:
            return lambda_response(400, {'error': 'Email and password are required'})
        
        # Check user credentials
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, name, email, organization_id, password 
                FROM users 
                WHERE email = %s
            """, (email,))
            
            user = cur.fetchone()
            if not user:
                return lambda_response(401, {'error': 'Invalid credentials'})
            
            # Verify password using bcrypt
            if not verify_password(password, user['password']):
                return lambda_response(401, {'error': 'Invalid credentials'})
            
            # Create session token (simple approach)
            session_data = {
                'user_id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'organization_id': user['organization_id'],
                'exp': int((datetime.now() + timedelta(days=7)).timestamp())
            }
            
            return lambda_response(200, {
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'organization_id': user['organization_id']
                },
                'session': session_data
            })
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return lambda_response(500, {'error': 'Login failed'})

def register_handler(event, context):
    """POST /register - User registration"""
    try:
        # Parse request body
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body']).decode('utf-8')
        else:
            body = event['body']
        
        request_data = json.loads(body)
        name = request_data.get('name', '').strip()
        email = request_data.get('email', '').strip().lower()
        password = request_data.get('password', '')
        organization_name = request_data.get('organization', '').strip()
        
        if not all([name, email, password]):
            return lambda_response(400, {'error': 'Name, email, and password are required'})
        
        with get_db_cursor() as cur:
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return lambda_response(400, {'error': 'User already exists'})
            
            # Create organization if provided
            org_id = ORG_ID  # Default org
            if organization_name:
                org_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO organizations (id, name, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                """, (org_id, organization_name))
            
            # Create user with hashed password
            user_id = str(uuid.uuid4())
            hashed_password = hash_password(password)
            cur.execute("""
                INSERT INTO users (id, name, email, organization_id, password, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """, (user_id, name, email, org_id, hashed_password))
            
            return lambda_response(201, {
                'message': 'Registration successful',
                'user': {
                    'id': user_id,
                    'name': name,
                    'email': email,
                    'organization_id': org_id
                }
            })
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return lambda_response(500, {'error': 'Registration failed'})

def auth_current_handler(event, context):
    """GET /auth/current - Get current user from session"""
    try:
        # Check for session data in headers (from Authorization header)
        session_data = None
        headers = event.get('headers', {})
        
        # Check Authorization header
        auth_header = headers.get('Authorization') or headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_str = auth_header[7:]  # Remove 'Bearer ' prefix
            try:
                session_data = json.loads(session_str)
            except:
                pass
        
        # Fallback: Check query parameters
        if not session_data and event.get('queryStringParameters') and event['queryStringParameters'].get('session'):
            session_str = event['queryStringParameters']['session']
            try:
                session_data = json.loads(session_str)
            except:
                pass
        
        if not session_data:
            return lambda_response(401, {'error': 'Not authenticated'})
        
        # Verify session hasn't expired
        if session_data.get('exp', 0) < datetime.now().timestamp():
            return lambda_response(401, {'error': 'Session expired'})
        
        return lambda_response(200, {
            'user': {
                'id': session_data['user_id'],
                'name': session_data.get('name', ''),
                'email': session_data.get('email', ''),
                'organization_id': session_data.get('organization_id', '')
            }
        })
        
    except Exception as e:
        logger.error(f"Auth current error: {str(e)}")
        return lambda_response(401, {'error': 'Authentication failed'})