#!/bin/bash

# GenAI Accounting System - Model Selection Deployment Script

echo "🦙 GenAI Accounting System - AI Model Deployment"
echo "================================================="

# Available models
echo ""
echo "Available AI Models:"
echo ""
echo "🦙 Meta Llama Models (Recommended):"
echo "  1) meta.llama3-2-1b-instruct-v1:0   - Fastest, lowest cost"
echo "  2) meta.llama3-2-3b-instruct-v1:0   - ⭐ RECOMMENDED (default)"
echo "  3) meta.llama3-2-11b-instruct-v1:0  - High accuracy"
echo "  4) meta.llama3-2-90b-instruct-v1:0  - Maximum accuracy"
echo ""
echo "🎯 Mistral Models:"
echo "  5) mistral.mistral-7b-instruct-v0:2    - Balanced performance"
echo "  6) mistral.mixtral-8x7b-instruct-v0:1  - Mixture of experts"
echo "  7) mistral.mistral-large-2407-v1:0     - Latest, best accuracy"
echo ""
echo "⭐ Amazon Nova Models:"
echo "  8) amazon.nova-micro-v1:0  - Ultra-fast, cost-effective"
echo "  9) amazon.nova-lite-v1:0   - Balanced performance"
echo " 10) amazon.nova-pro-v1:0    - Professional grade"
echo ""
echo "🧠 Claude Models (Legacy):"
echo " 11) anthropic.claude-3-5-sonnet-20240620-v1:0"
echo " 12) anthropic.claude-3-haiku-20240307-v1:0"
echo ""

read -p "Select model number (1-12) or press Enter for default [2]: " choice

# Model mapping
case $choice in
    1) MODEL_ID="meta.llama3-2-1b-instruct-v1:0" ;;
    2|"") MODEL_ID="meta.llama3-2-3b-instruct-v1:0" ;;
    3) MODEL_ID="meta.llama3-2-11b-instruct-v1:0" ;;
    4) MODEL_ID="meta.llama3-2-90b-instruct-v1:0" ;;
    5) MODEL_ID="mistral.mistral-7b-instruct-v0:2" ;;
    6) MODEL_ID="mistral.mixtral-8x7b-instruct-v0:1" ;;
    7) MODEL_ID="mistral.mistral-large-2407-v1:0" ;;
    8) MODEL_ID="amazon.nova-micro-v1:0" ;;
    9) MODEL_ID="amazon.nova-lite-v1:0" ;;
    10) MODEL_ID="amazon.nova-pro-v1:0" ;;
    11) MODEL_ID="anthropic.claude-3-5-sonnet-20240620-v1:0" ;;
    12) MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0" ;;
    *) MODEL_ID="meta.llama3-2-3b-instruct-v1:0" ;;
esac

echo ""
echo "Selected Model: $MODEL_ID"
echo ""

# Ask for other parameters if first deployment
if [ ! -f samconfig.toml ]; then
    echo "🚀 First-time deployment detected. You'll need to provide configuration:"
    echo ""
    read -p "Stack name [genai-accounting]: " STACK_NAME
    STACK_NAME=${STACK_NAME:-genai-accounting}
    
    read -p "AWS Region [ap-southeast-1]: " AWS_REGION
    AWS_REGION=${AWS_REGION:-ap-southeast-1}
    
    echo ""
    echo "📊 Database Configuration:"
    read -p "PostgreSQL Host (RDS endpoint): " DB_HOST
    read -p "Database Name [accounting]: " DB_NAME
    DB_NAME=${DB_NAME:-accounting}
    read -p "Database User: " DB_USER
    read -s -p "Database Password: " DB_PASSWORD
    echo ""
    read -p "Organization ID (UUID): " ORG_ID
    
    echo ""
    echo "🏗️  Building and deploying with guided setup..."
    sam build
    sam deploy --guided \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --parameter-overrides \
            ModelId="$MODEL_ID" \
            DatabaseHost="$DB_HOST" \
            DatabaseName="$DB_NAME" \
            DatabaseUser="$DB_USER" \
            DatabasePassword="$DB_PASSWORD" \
            OrganizationId="$ORG_ID"
else
    echo "📦 Existing deployment detected. Updating model only..."
    sam build
    sam deploy --parameter-overrides ModelId="$MODEL_ID"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔧 Next Steps:"
echo "1. Upload frontend files to your S3 website bucket"
echo "2. Test receipt upload with your new AI model"
echo "3. Monitor CloudWatch logs for model performance"
echo ""
echo "📚 For model performance comparison, see AI_MODELS.md"
echo ""