import os
import json
import base64
import boto3
from datetime import datetime

# Simple unified AI chat handler
def ai_chat_handler(event, context):
    """POST /ai/chat - Simple unified AI for all accounting tasks"""
    
    try:
        # Parse request
        if event.get('isBase64Encoded', False):
            body = json.loads(base64.b64decode(event['body']).decode('utf-8'))
        else:
            body = json.loads(event['body'])
        
        # Handle different request types
        if 'message' in body:
            # Regular chat message
            user_message = body['message']
            response_text = get_ai_response(user_message)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    'message': user_message,
                    'response': response_text,
                    'timestamp': datetime.now().isoformat()
                })
            }
            
        elif 'ocr_text' in body:
            # Receipt classification request
            ocr_text = body['ocr_text']
            category = classify_receipt(ocr_text)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    'category': category,
                    'confidence': 0.85,
                    'original_text': ocr_text[:100] + '...' if len(ocr_text) > 100 else ocr_text,
                    'timestamp': datetime.now().isoformat()
                })
            }
            
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({'error': 'Either message or ocr_text is required'})
            }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def get_ai_response(user_message: str) -> str:
    """Simple AI response using Bedrock"""
    
    prompt = f"""You are Hackybara AI, an expert accounting assistant for small and medium businesses. 

You help with:
• Financial reports and expense tracking
• Cash flow predictions and budgeting  
• Tax preparation and planning
• General accounting questions
• Business financial insights

User question: {user_message}

Provide helpful, practical, and actionable advice. Keep responses business-focused and easy to understand."""
    
    try:
        # Use Bedrock
        bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('BEDROCK_REGION', 'ap-southeast-1'))
        
        # Nova Lite model request format
        request_body = {
            "messages": [
                {
                    "role": "user", 
                    "content": [{"type": "text", "text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 1000,
                "temperature": 0.3,
                "topP": 0.9
            }
        }
        
        response = bedrock.invoke_model(
            modelId=os.environ.get('MODEL_ID', 'amazon.nova-lite-v1:0'),
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['output']['message']['content'][0]['text']
        
    except Exception as e:
        print(f"Bedrock error: {str(e)}")
        return f"I'm having trouble connecting right now, but I'd be happy to help with your accounting question: {user_message}. Please try again in a moment."

def classify_receipt(ocr_text: str) -> str:
    """Classify receipt using AI"""
    
    prompt = f"""Classify this receipt into exactly one of these categories:
- Food & Beverage
- Utilities 
- Transportation
- Office Supplies
- Others

Receipt text: {ocr_text[:1000]}

Respond with ONLY the category name."""
    
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('BEDROCK_REGION', 'ap-southeast-1'))
        
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 50,
                "temperature": 0.1,
                "topP": 0.5
            }
        }
        
        response = bedrock.invoke_model(
            modelId=os.environ.get('MODEL_ID', 'amazon.nova-lite-v1:0'),
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        category = response_body['output']['message']['content'][0]['text'].strip()
        
        # Validate category
        valid_categories = ["Food & Beverage", "Utilities", "Transportation", "Office Supplies", "Others"]
        for valid_cat in valid_categories:
            if valid_cat.lower() in category.lower():
                return valid_cat
                
        return "Others"  # Default fallback
        
    except Exception as e:
        print(f"Classification error: {str(e)}")
        # Simple keyword fallback
        text_lower = ocr_text.lower()
        if any(word in text_lower for word in ['coffee', 'restaurant', 'food', 'meal', 'starbucks', 'mcdonald']):
            return "Food & Beverage"
        elif any(word in text_lower for word in ['electric', 'utility', 'water', 'gas', 'internet']):
            return "Utilities"
        elif any(word in text_lower for word in ['taxi', 'uber', 'transport', 'fuel', 'parking']):
            return "Transportation"
        elif any(word in text_lower for word in ['office', 'supplies', 'paper', 'pen']):
            return "Office Supplies"
        else:
            return "Others"