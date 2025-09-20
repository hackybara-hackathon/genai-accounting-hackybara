import json
import boto3
import logging
import os
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
TABLE_NAME = os.environ['TABLE_NAME']

# DynamoDB table
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda handler for generating spending summary and KPIs
    """
    try:
        logger.info("Generating spending summary")
        
        # Scan DynamoDB table to get all receipts
        response = table.scan()
        items = response['Items']
        
        # Continue scanning if there are more items (pagination)
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])
        
        # Aggregate data by category
        category_totals = {}
        total_expense = Decimal('0')
        receipt_count = len(items)
        
        for item in items:
            category = item.get('category', 'Others')
            amount = item.get('total_amount', Decimal('0'))
            
            # Ensure amount is Decimal
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
            
            category_totals[category] = category_totals.get(category, Decimal('0')) + amount
            total_expense += amount
        
        # Create summary array
        summary = []
        for category, total in category_totals.items():
            summary.append({
                'category': category,
                'total': float(total)
            })
        
        # Sort by total descending
        summary.sort(key=lambda x: x['total'], reverse=True)
        
        # Calculate KPIs
        avg_per_receipt = float(total_expense / receipt_count) if receipt_count > 0 else 0
        top_category = summary[0]['category'] if summary else 'None'
        
        kpis = {
            'total_expense': float(total_expense),
            'receipt_count': receipt_count,
            'avg_per_receipt': round(avg_per_receipt, 2),
            'top_category': top_category
        }
        
        result = {
            'summary': summary,
            'kpis': kpis
        }
        
        logger.info(f"Generated summary with {len(summary)} categories, {receipt_count} receipts")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }