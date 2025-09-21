#!/bin/bash
# Full deployment script for both backend and frontend
# Usage: ./deploy-full.sh

set -e

echo "🚀 Starting full deployment (SAM + S3 Website)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REGION="ap-southeast-1"
STACK_NAME="genai-accounting-simple"

echo -e "${CYAN}📦 Step 1: Building SAM application...${NC}"
sam build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ SAM build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ SAM build completed${NC}"

echo -e "${CYAN}🚀 Step 2: Deploying SAM stack...${NC}"
sam deploy

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ SAM deploy failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ SAM stack deployed${NC}"

echo -e "${CYAN}🌐 Step 3: Getting S3 bucket name from stack outputs...${NC}"
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`WebsiteBucketName`].OutputValue' \
    --output text)

if [ -z "$BUCKET_NAME" ]; then
    echo -e "${RED}❌ Could not retrieve S3 bucket name from stack${NC}"
    exit 1
fi

echo -e "${YELLOW}📁 Website bucket: $BUCKET_NAME${NC}"

echo -e "${CYAN}📂 Step 4: Syncing frontend files to S3...${NC}"

# Sync HTML files (frontend/layout -> S3 root)
echo "  • Syncing HTML files..."
aws s3 sync frontend/layout/ s3://$BUCKET_NAME/ \
    --include "*.html" \
    --cache-control "max-age=300" \
    --delete

# Sync CSS files  
echo "  • Syncing CSS files..."
aws s3 sync css/ s3://$BUCKET_NAME/css/ \
    --include "*.css" \
    --cache-control "max-age=86400" \
    --delete

# Sync JS files
echo "  • Syncing JavaScript files..."
aws s3 sync frontend/js/ s3://$BUCKET_NAME/js/ \
    --include "*.js" \
    --cache-control "max-age=86400" \
    --delete

echo -e "${CYAN}🔓 Step 5: Setting bucket policy for public access...${NC}"
cat > /tmp/bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file:///tmp/bucket-policy.json
rm /tmp/bucket-policy.json

# Get website URL
WEBSITE_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`WebsiteUrl`].OutputValue' \
    --output text)

# Get API URL  
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${CYAN}🌐 Website URL: $WEBSITE_URL${NC}"
echo -e "${CYAN}🔗 API URL: $API_URL${NC}"
echo -e "${YELLOW}📊 Cache Settings:${NC}"
echo -e "   • HTML files: 5 minutes (quick updates)"
echo -e "   • CSS/JS files: 24 hours (performance)"
echo ""