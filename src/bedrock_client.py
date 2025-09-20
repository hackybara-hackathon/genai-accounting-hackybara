import json
import boto3
import logging
import os
import re
from typing import Optional, Dict, List

logger = logging.getLogger()

class BedrockClient:
    def __init__(self):
        region = os.environ.get('AWS_REGION', 'ap-southeast-1')
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = os.environ.get('MODEL_ID', 'anthropic.claude-3-5-sonnet-20240620-v1:0')
        
    def classify_receipt(self, text: str) -> Optional[str]:
        """
        Classify receipt using Amazon Bedrock
        """
        if not text:
            return None
        
        try:
            # Truncate text to avoid token limits
            text_sample = text[:2000]
            
            prompt = f"""You are a strict receipt categorizer for SMEs.
Return ONLY a JSON object with a single key "category".
The value MUST be one of: ["Food & Beverage","Utilities","Transportation","Office Supplies","Others"].
If unsure, choose "Others".
Receipt text:
{text_sample}
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
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                
                # Extract JSON from response
                json_match = re.search(r'\{[^}]*"category"[^}]*\}', text_content)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        category = result.get('category')
                        
                        # Validate category
                        valid_categories = ["Food & Beverage", "Utilities", "Transportation", "Office Supplies", "Others"]
                        if category in valid_categories:
                            logger.info(f"Bedrock classified as: {category}")
                            return category
                    except json.JSONDecodeError:
                        pass
            
            logger.warning("Bedrock returned invalid category format")
            return None
            
        except Exception as e:
            logger.error(f"Bedrock classification failed: {str(e)}")
            return None

    def generate_insights(self, context_data: Dict) -> Dict[str, any]:
        """
        Generate business insights using Bedrock with grounded context
        """
        try:
            # Prepare context summary
            context_json = json.dumps(context_data, indent=2)[:4000]  # Limit context size
            
            prompt = f"""You are a financial advisor for SMEs. Based ONLY on the provided financial data, generate insights and recommendations.

Financial Context:
{context_json}

Provide a response in this EXACT format:

---SUMMARY---
[Write 120-180 words summarizing the financial situation with 2-3 concrete actionable recommendations based on the data provided]

---JSON---
{{
  "budget_recommendations": [
    {{
      "category": "category_name",
      "suggestion": "specific recommendation",
      "est_monthly_savings": 0
    }}
  ],
  "tax_preparation": [
    {{
      "item": "preparation_item",
      "why_it_matters": "explanation"
    }}
  ],
  "risks": [
    {{
      "risk": "identified_risk",
      "watch_metric": "metric_to_monitor"
    }}
  ]
}}

Use ONLY the data provided. Do not make assumptions about data not present."""

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.3,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                
                # Extract summary and JSON sections
                summary_match = re.search(r'---SUMMARY---\s*(.*?)\s*---JSON---', text_content, re.DOTALL)
                json_match = re.search(r'---JSON---\s*(\{.*\})', text_content, re.DOTALL)
                
                if summary_match and json_match:
                    try:
                        summary = summary_match.group(1).strip()
                        actions_json = json.loads(json_match.group(1))
                        
                        return {
                            'summary': summary,
                            'actions': actions_json
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse insights JSON: {e}")
            
            # Fallback response
            return {
                'summary': 'Unable to generate detailed insights. Please ensure you have sufficient transaction data for analysis.',
                'actions': {
                    'budget_recommendations': [],
                    'tax_preparation': [],
                    'risks': []
                }
            }
            
        except Exception as e:
            logger.error(f"Insights generation failed: {str(e)}")
            return {
                'summary': f'Insights generation temporarily unavailable due to: {str(e)[:100]}',
                'actions': {
                    'budget_recommendations': [],
                    'tax_preparation': [],
                    'risks': []
                }
            }

def keyword_guess(text: str) -> str:
    """
    Fallback keyword-based classification
    """
    if not text:
        return "Others"
    
    text_lower = text.lower()
    
    # Category keyword mappings with more comprehensive lists
    category_keywords = {
        "Food & Beverage": [
            # Restaurants & Fast Food
            'kfc', 'mcdonald', 'burger king', 'pizza hut', 'domino', 'subway',
            'starbucks', 'coffee bean', 'old town', 'kopitiam', 'mamak',
            'restaurant', 'cafe', 'bistro', 'diner', 'eatery', 'kitchen',
            # Food Types
            'food', 'meal', 'lunch', 'dinner', 'breakfast', 'brunch',
            'drink', 'beverages', 'coffee', 'tea', 'juice', 'water',
            'beer', 'wine', 'alcohol', 'bar', 'pub', 'lounge',
            # Food Shopping
            'grocery', 'supermarket', 'market', 'hypermarket', 'mart',
            'giant', 'tesco', 'aeon', 'jaya grocer', 'cold storage',
            'bakery', 'pastry', 'bread', 'cake', 'dessert',
            # Malaysian specific
            'nasi', 'mee', 'char kuey teow', 'roti', 'teh tarik', 'kopi'
        ],
        "Utilities": [
            # Electricity & Power
            'electric', 'electricity', 'power', 'energy', 'tnb', 'tenaga',
            'electric bill', 'power bill', 'utility bill',
            # Water
            'water', 'air', 'syabas', 'pba', 'sab', 'water bill',
            # Gas
            'gas', 'lpg', 'natural gas', 'petronas gas',
            # Internet & Telecommunications
            'internet', 'broadband', 'wifi', 'telekom', 'tm', 'unifi',
            'maxis', 'celcom', 'digi', 'u mobile', 'yes', 'time',
            'phone', 'mobile', 'postpaid', 'prepaid', 'data plan',
            # Utilities General
            'utility', 'utilities', 'bill', 'monthly bill'
        ],
        "Transportation": [
            # Ride Hailing
            'grab', 'uber', 'gojek', 'taxi', 'e-hailing',
            # Public Transport
            'bus', 'train', 'mrt', 'lrt', 'kl monorail', 'rapidkl',
            'ktm', 'ets', 'klia ekspres', 'public transport',
            # Fuel
            'petrol', 'gasoline', 'diesel', 'fuel', 'gas station',
            'petronas', 'shell', 'esso', 'bhp', 'caltex',
            # Parking & Tolls
            'parking', 'toll', 'highway', 'plus', 'smart tag',
            'touch n go', 'parking fee', 'toll fee',
            # Vehicle Services
            'car wash', 'service center', 'workshop', 'mechanic',
            'vehicle', 'automotive', 'motorcycle', 'motor',
            # Air Travel
            'flight', 'airline', 'airport', 'airasia', 'mas',
            'malindo', 'firefly', 'aviation', 'boarding'
        ],
        "Office Supplies": [
            # Stationery
            'office', 'stationery', 'stationary', 'paper', 'pen', 'pencil',
            'marker', 'highlighter', 'stapler', 'clip', 'folder',
            'notebook', 'notepad', 'file', 'binder', 'envelope',
            # Technology
            'computer', 'laptop', 'desktop', 'monitor', 'keyboard',
            'mouse', 'printer', 'scanner', 'toner', 'ink', 'cartridge',
            'software', 'hardware', 'it equipment', 'electronics',
            # Furniture
            'desk', 'chair', 'table', 'cabinet', 'shelf', 'furniture',
            'office furniture', 'ergonomic', 'workstation',
            # Supplies
            'supplies', 'equipment', 'materials', 'tools',
            # Office Stores
            'popular bookstore', 'mph', 'office depot', 'staples'
        ]
    }
    
    # Count matches for each category with weighted scoring
    category_scores = {}
    for category, keywords in category_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                # Longer keywords get higher weight
                weight = len(keyword.split()) * 2 if len(keyword.split()) > 1 else 1
                score += weight
        
        if score > 0:
            category_scores[category] = score
    
    # Return category with highest score, or "Others" if no matches
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        logger.info(f"Keyword classification: {best_category} (score: {category_scores[best_category]})")
        return best_category
    
    return "Others"

# Initialize global client
bedrock_client = BedrockClient()