import json
import boto3
import logging
import os
import re
from typing import Optional, Dict, List

logger = logging.getLogger()

class BedrockClient:
    def __init__(self):
        region = os.environ.get('BEDROCK_REGION', 'ap-southeast-1')
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = os.environ.get('MODEL_ID', 'meta.llama3-2-3b-instruct-v1:0')
        
        # Model configurations
        self.model_configs = {
            # Meta Llama models
            'meta.llama3-2-1b-instruct-v1:0': {'type': 'llama', 'max_tokens': 2048},
            'meta.llama3-2-3b-instruct-v1:0': {'type': 'llama', 'max_tokens': 2048},
            'meta.llama3-2-11b-instruct-v1:0': {'type': 'llama', 'max_tokens': 2048},
            'meta.llama3-2-90b-instruct-v1:0': {'type': 'llama', 'max_tokens': 2048},
            'meta.llama3-1-8b-instruct-v1:0': {'type': 'llama', 'max_tokens': 2048},
            'meta.llama3-1-70b-instruct-v1:0': {'type': 'llama', 'max_tokens': 2048},
            
            # Mistral models
            'mistral.mistral-7b-instruct-v0:2': {'type': 'mistral', 'max_tokens': 4096},
            'mistral.mixtral-8x7b-instruct-v0:1': {'type': 'mistral', 'max_tokens': 4096},
            'mistral.mistral-large-2402-v1:0': {'type': 'mistral', 'max_tokens': 4096},
            'mistral.mistral-large-2407-v1:0': {'type': 'mistral', 'max_tokens': 4096},
            
            # Amazon Nova models (when available)
            'amazon.nova-micro-v1:0': {'type': 'nova', 'max_tokens': 2048},
            'amazon.nova-lite-v1:0': {'type': 'nova', 'max_tokens': 2048},
            'amazon.nova-pro-v1:0': {'type': 'nova', 'max_tokens': 2048},
            
            # DeepSeek (via custom integration)
            'deepseek-chat': {'type': 'deepseek', 'max_tokens': 4096},
            'deepseek-coder': {'type': 'deepseek', 'max_tokens': 4096},
            
            # Legacy Claude support
            'anthropic.claude-3-5-sonnet-20240620-v1:0': {'type': 'claude', 'max_tokens': 4096},
            'anthropic.claude-3-haiku-20240307-v1:0': {'type': 'claude', 'max_tokens': 4096}
        }
        
        # Get model configuration
        self.model_config = self.model_configs.get(self.model_id, {'type': 'llama', 'max_tokens': 2048})
        self.model_type = self.model_config['type']
        
    def classify_receipt(self, text: str) -> Optional[str]:
        """
        Classify receipt using Amazon Bedrock with multiple model support
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

            # Prepare request body based on model type
            body = self._prepare_request_body(prompt, max_tokens=100, temperature=0)
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            text_content = self._extract_response_text(response_body)
            
            if text_content:
                # Extract JSON from response
                json_match = re.search(r'\{[^}]*"category"[^}]*\}', text_content)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        category = result.get('category')
                        
                        # Validate category
                        valid_categories = ["Food & Beverage", "Utilities", "Transportation", "Office Supplies", "Others"]
                        if category in valid_categories:
                            logger.info(f"{self.model_type.upper()} classified as: {category}")
                            return category
                    except json.JSONDecodeError:
                        pass
            
            logger.warning(f"{self.model_type.upper()} returned invalid category format")
            return None
            
        except Exception as e:
            logger.error(f"{self.model_type.upper()} classification failed: {str(e)}")
            return None

    def _prepare_request_body(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.0) -> str:
        """
        Prepare request body based on model type
        """
        if self.model_type == 'claude':
            return json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        
        elif self.model_type == 'llama':
            return json.dumps({
                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "max_gen_len": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            })
        
        elif self.model_type == 'mistral':
            return json.dumps({
                "prompt": f"<s>[INST] {prompt} [/INST]",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 50
            })
        
        elif self.model_type == 'nova':
            return json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                }
            })
        
        elif self.model_type == 'deepseek':
            # DeepSeek would require custom API integration
            return json.dumps({
                "model": self.model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            })
        
        else:
            # Default to Llama format
            return json.dumps({
                "prompt": prompt,
                "max_gen_len": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            })

    def _extract_response_text(self, response_body: dict) -> Optional[str]:
        """
        Extract text from response based on model type
        """
        try:
            if self.model_type == 'claude':
                content = response_body.get('content', [])
                if content and len(content) > 0:
                    return content[0].get('text', '')
            
            elif self.model_type == 'llama':
                return response_body.get('generation', '')
            
            elif self.model_type == 'mistral':
                outputs = response_body.get('outputs', [])
                if outputs and len(outputs) > 0:
                    return outputs[0].get('text', '')
            
            elif self.model_type == 'nova':
                output = response_body.get('output', {})
                message = output.get('message', {})
                content = message.get('content', [])
                if content and len(content) > 0:
                    return content[0].get('text', '')
            
            elif self.model_type == 'deepseek':
                choices = response_body.get('choices', [])
                if choices and len(choices) > 0:
                    message = choices[0].get('message', {})
                    return message.get('content', '')
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting response text: {str(e)}")
            return None

    def generate_insights(self, context_data: Dict) -> Dict[str, any]:
        """
        Generate business insights using multiple AI models with grounded context
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

            # Prepare request body based on model type
            body = self._prepare_request_body(prompt, max_tokens=1000, temperature=0.3)
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            text_content = self._extract_response_text(response_body)
            
            if text_content:
                # Extract summary and JSON sections
                summary_match = re.search(r'---SUMMARY---\s*(.*?)\s*---JSON---', text_content, re.DOTALL)
                json_match = re.search(r'---JSON---\s*(\{.*\})', text_content, re.DOTALL)
                
                if summary_match and json_match:
                    try:
                        summary = summary_match.group(1).strip()
                        actions_json = json.loads(json_match.group(1))
                        
                        logger.info(f"Generated insights using {self.model_type.upper()}")
                        return {
                            'summary': summary,
                            'actions': actions_json,
                            'model_used': self.model_type
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse insights JSON: {e}")
            
            # Fallback response
            return {
                'summary': f'Unable to generate detailed insights using {self.model_type.upper()}. Please ensure you have sufficient transaction data for analysis.',
                'actions': {
                    'budget_recommendations': [],
                    'tax_preparation': [],
                    'risks': []
                },
                'model_used': self.model_type
            }
            
        except Exception as e:
            logger.error(f"Insights generation failed with {self.model_type.upper()}: {str(e)}")
            return {
                'summary': f'Insights generation temporarily unavailable using {self.model_type.upper()} due to: {str(e)[:100]}',
                'actions': {
                    'budget_recommendations': [],
                    'tax_preparation': [],
                    'risks': []
                },
                'model_used': self.model_type
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

    def tax_preparation_advisor(self, user_query: str, transaction_data: Dict = None) -> str:
        """
        AI Tax Preparation Assistant - Provides guidance on tax preparation,
        deductions, and compliance based on user's financial data
        """
        context = ""
        if transaction_data:
            context = f"""
User's Financial Context:
- Total Expenses: ${transaction_data.get('total_expenses', 0):,.2f}
- Business Expenses: ${transaction_data.get('business_expenses', 0):,.2f}
- Receipt Count: {transaction_data.get('receipt_count', 0)}
- Top Categories: {', '.join(transaction_data.get('top_categories', []))}
"""

        prompt = f"""You are a professional tax preparation advisor with expertise in small business and personal tax planning. 

{context}

User Question: {user_query}

Please provide specific, actionable tax advice including:
1. Relevant tax deductions and strategies
2. Required documentation and record-keeping
3. Deadlines and compliance requirements
4. Potential tax-saving opportunities
5. Next steps for implementation

Keep your advice practical and cite relevant tax regulations when appropriate."""

        try:
            return self._make_bedrock_call(prompt)
        except Exception as e:
            logger.error(f"Tax advisor error: {str(e)}")
            return "I apologize, but I'm unable to provide tax advice at the moment. Please consult with a qualified tax professional for personalized guidance."

    def financial_advisor(self, user_query: str, financial_summary: Dict = None) -> str:
        """
        AI Financial Advisor - Provides personalized financial advice based on
        spending patterns, cash flow, and financial goals
        """
        context = ""
        if financial_summary:
            context = f"""
User's Financial Profile:
- Monthly Average Spending: ${financial_summary.get('monthly_avg', 0):,.2f}
- Cash Flow Trend: {financial_summary.get('trend', 'Unknown')}
- Largest Expense Categories: {', '.join(financial_summary.get('top_categories', []))}
- Spending Variance: {financial_summary.get('variance', 'Stable')}
- Recent Transactions: {financial_summary.get('recent_count', 0)}
"""

        prompt = f"""You are a certified financial advisor with expertise in personal finance, budgeting, and investment planning.

{context}

User Question: {user_query}

Please provide comprehensive financial advice including:
1. Analysis of current spending patterns
2. Specific recommendations for improvement
3. Actionable steps to achieve financial goals
4. Risk assessment and mitigation strategies
5. Long-term financial planning suggestions

Make your advice practical, measurable, and tailored to the user's financial situation."""

        try:
            return self._make_bedrock_call(prompt)
        except Exception as e:
            logger.error(f"Financial advisor error: {str(e)}")
            return "I'm currently unable to provide financial advice. Please try again later or consult with a financial advisor."

    def budget_recommendations(self, spending_data: Dict, user_goals: str = "") -> str:
        """
        AI Budget Advisor - Creates personalized budget recommendations based on
        historical spending patterns and financial goals
        """
        total_spending = spending_data.get('total_spending', 0)
        category_breakdown = spending_data.get('categories', {})
        monthly_trend = spending_data.get('monthly_trend', 'stable')
        
        category_analysis = ""
        for category, amount in category_breakdown.items():
            percentage = (amount / total_spending * 100) if total_spending > 0 else 0
            category_analysis += f"- {category}: ${amount:,.2f} ({percentage:.1f}%)\n"

        prompt = f"""You are a professional budget planning expert specializing in personal and small business financial management.

CURRENT SPENDING ANALYSIS:
Total Monthly Spending: ${total_spending:,.2f}
Spending Trend: {monthly_trend}

Category Breakdown:
{category_analysis}

User Goals: {user_goals or 'Not specified'}

Please create a comprehensive budget recommendation including:

1. SPENDING ANALYSIS:
   - Identify areas of overspending
   - Highlight efficient spending categories
   - Compare to recommended budget percentages

2. PERSONALIZED BUDGET PLAN:
   - Suggested monthly limits per category
   - Specific reduction targets for overspending areas
   - Reallocation recommendations

3. ACTIONABLE STRATEGIES:
   - 3-5 specific steps to reduce expenses
   - Tools and methods for tracking progress
   - Timeline for achieving budget goals

4. SAVINGS OPPORTUNITIES:
   - Immediate cost-cutting possibilities
   - Long-term optimization strategies
   - Emergency fund recommendations

Make your recommendations specific, realistic, and achievable based on the user's current spending patterns."""

        try:
            return self._make_bedrock_call(prompt)
        except Exception as e:
            logger.error(f"Budget recommendations error: {str(e)}")
            return "I'm unable to generate budget recommendations at the moment. Please ensure your financial data is available and try again."

    def general_ai_chat(self, user_message: str, conversation_context: List[Dict] = None) -> str:
        """
        General AI Assistant for accounting, finance, and business questions
        """
        context = ""
        if conversation_context:
            context = "Previous conversation:\n"
            for msg in conversation_context[-3:]:  # Last 3 messages for context
                context += f"{msg.get('role', 'user')}: {msg.get('message', '')}\n"
            context += "\n"

        prompt = f"""You are an intelligent assistant specializing in accounting, finance, business management, and tax preparation. You provide helpful, accurate, and professional advice.

{context}Current question: {user_message}

Please provide a comprehensive and helpful response. If the question is about:
- Accounting: Provide clear explanations with examples
- Finance: Offer practical advice and calculations when relevant
- Tax matters: Give general guidance but recommend consulting professionals for specific situations
- Business: Share actionable insights and best practices

Keep your response informative yet accessible, and always prioritize accuracy and helpfulness."""

        try:
            return self._make_bedrock_call(prompt)
        except Exception as e:
            logger.error(f"General chat error: {str(e)}")
            return "I apologize, but I'm experiencing technical difficulties. Please try your question again."

# Initialize global client - updated with AI enhancements
bedrock_client = BedrockClient()