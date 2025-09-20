# GenAI-Enhanced Accounting Management System

A production-ready serverless API for automated receipt processing and categorization using PostgreSQL, AWS Lambda, and Amazon Bedrock AI.

## Architecture

- **Frontend**: Static website hosted on S3
- **Backend**: AWS Lambda functions with API Gateway
- **Database**: PostgreSQL RDS with comprehensive accounting schema
- **Storage**: S3 for receipt files
- **AI**: Amazon Bedrock for intelligent categorization and business insights
- **Monitoring**: CloudWatch logs

## Quick Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- **PostgreSQL RDS instance** already created and accessible
- Database schema already created (see Database Schema section)

### One-Command Deploy

```bash
sam build
sam deploy --guided
```

During the guided deployment, you'll be prompted for:
- Stack name (e.g., `genai-accounting`)
- AWS region (recommend `ap-southeast-1` or `us-east-1` for Bedrock)
- S3 bucket names (will be auto-suffixed with account ID)
- Bedrock model ID (default: `anthropic.claude-3-5-sonnet-20240620-v1:0`)
- **PostgreSQL connection details**:
  - Database host (RDS endpoint)
  - Database port (default: 5432)
  - Database name
  - Database username
  - Database password (hidden input)
  - Organization ID (UUID for your organization)

### Post-Deployment Setup

1. **Update Website Configuration**
   - Copy the API Gateway URL from the deployment outputs
   - Edit `web/index.html` and replace `<<<REPLACE_WITH_API_URL>>>` with your actual API URL
   - Upload the updated `web/index.html` to your website S3 bucket

2. **Upload Website Files**
   ```bash
   aws s3 cp web/index.html s3://YOUR-WEBSITE-BUCKET-NAME/
   ```

3. **Enable CORS (if needed)**
   The template automatically configures CORS, but if you encounter issues:
   - API Gateway CORS is set to allow all origins (`*`)
   - S3 buckets have CORS configured for cross-origin requests

## Bedrock Model Configuration

### Supported Models & Regions
- **ap-southeast-1 (Singapore)**: `anthropic.claude-3-5-sonnet-20240620-v1:0`
- **us-east-1 (N. Virginia)**: `anthropic.claude-3-5-sonnet-20240620-v1:0`

### Model Access
Ensure you have enabled model access in the Bedrock console for your chosen region:
1. Go to AWS Bedrock console
2. Navigate to "Model access" 
3. Enable access for Claude 3.5 Sonnet

## Database Schema

The system requires PostgreSQL with the following tables in the `public` schema:

```sql
-- Organizations table
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents table
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  name VARCHAR(255) NOT NULL,
  document_url TEXT NOT NULL,
  type VARCHAR(50) DEFAULT 'receipt',
  uploaded_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vendors table
CREATE TABLE vendors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(organization_id, name)
);

-- Categories table
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(organization_id, name)
);

-- Accounts table
CREATE TABLE accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  code VARCHAR(50),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(organization_id, name)
);

-- OCR Results table
CREATE TABLE ocr_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  document_id UUID REFERENCES documents(id),
  vendor_id UUID REFERENCES vendors(id),
  text TEXT,
  total_amount NUMERIC(12,2),
  currency VARCHAR(3) DEFAULT 'MYR',
  invoice_date DATE,
  invoice_number VARCHAR(100),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions table
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  document_id UUID REFERENCES documents(id),
  ocr_result_id UUID REFERENCES ocr_results(id),
  vendor_id UUID REFERENCES vendors(id),
  account_id UUID REFERENCES accounts(id),
  categories_id UUID REFERENCES categories(id),
  description TEXT,
  amount NUMERIC(12,2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'MYR',
  invoice_date DATE,
  type TEXT DEFAULT 'expense',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Forecasts table
CREATE TABLE forecasts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  horizon INTEGER NOT NULL,
  granularity TEXT NOT NULL,
  series JSONB,
  computed_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_transactions_org_date ON transactions(organization_id, COALESCE(invoice_date, created_at::date));
CREATE INDEX idx_ocr_results_org ON ocr_results(organization_id);
CREATE INDEX idx_documents_org ON documents(organization_id);
CREATE INDEX idx_vendors_org ON vendors(organization_id);
CREATE INDEX idx_categories_org ON categories(organization_id);
```

## API Endpoints

### 1. POST /classify
Upload and classify receipts with AI categorization.

```bash
curl -X POST $API_URL/classify \
  -H "Content-Type: application/json" \
  -d '{
    "file_base64": "BASE64_ENCODED_IMAGE_DATA",
    "filename": "receipt.jpg",
    "ocr_text": "KFC Restaurant Invoice #12345 Total: RM 45.90"
  }'
```

### 2. GET /transactions
List transactions with filtering and pagination.

```bash
curl "$API_URL/transactions?limit=20&offset=0&from=2025-01-01&to=2025-01-31&category=Food&vendor=KFC"
```

### 3. GET /summary
Get KPIs and spending breakdown.

```bash
curl "$API_URL/summary"
```

### 4. GET /report/monthly
Get monthly spending report by category.

```bash
curl "$API_URL/report/monthly?year=2025"
```

### 5. GET /forecast
Generate cash flow forecasting.

```bash
curl "$API_URL/forecast"
```

### 6. POST /insights
Get AI-powered business insights.

```bash
curl -X POST $API_URL/insights \
  -H "Content-Type: application/json" \
  -d '{"question": "How can I reduce my food expenses?"}'
```

## Features

### Receipt Processing
- **File Upload**: Supports images (JPG, PNG) and PDFs
- **OCR Integration**: Accepts pre-processed OCR text
- **Field Extraction**: Automatically parses vendor, date, invoice number, and total amount
- **AI Categorization**: Uses Bedrock for intelligent categorization into:
  - Food & Beverage
  - Utilities  
  - Transportation
  - Office Supplies
  - Others
- **Fallback Classification**: Keyword-based classification when Bedrock is unavailable

### Analytics Dashboard
- **KPI Cards**: Total expenses, receipt count, average per receipt, top category
- **Spending Chart**: Visual breakdown by category
- **Real-time Updates**: Refresh summary after each upload

## Cost Optimization

### Estimated Monthly Costs (100 receipts/month)
- **Lambda**: ~$0.10 (100 invocations × 1 second average)
- **DynamoDB**: ~$0.25 (on-demand pricing)
- **S3**: ~$0.10 (storage + requests)
- **API Gateway**: ~$0.35 (100 requests)
- **Bedrock**: ~$1.50 (Claude 3.5 Sonnet usage)
- **Total**: ~$2.30/month

### Cost-Saving Features
- Pay-per-request pricing for all services
- Keyword fallback reduces Bedrock usage
- Minimal Lambda memory allocation (256MB)
- S3 lifecycle policies can be added for old receipts

## Security

### IAM Permissions (Least Privilege)
- Lambda functions have minimal required permissions
- S3 access scoped to specific buckets
- DynamoDB access limited to the receipts table
- Bedrock access restricted to the specified model

### Data Protection
- Receipt files stored securely in S3
- No sensitive data in logs
- HTTPS-only API endpoints

## Troubleshooting

### Common Issues

1. **Bedrock Access Denied**
   - Ensure model access is enabled in Bedrock console
   - Verify region supports the chosen model
   - Check IAM permissions for `bedrock:InvokeModel`

2. **CORS Errors**
   - Verify API Gateway CORS configuration
   - Ensure website URL matches CORS settings
   - Check browser developer tools for specific CORS errors

3. **File Upload Failures**
   - Check file size limits (API Gateway: 10MB)
   - Verify base64 encoding is correct
   - Ensure S3 bucket permissions are correct

### Debugging
- Check CloudWatch logs for Lambda function errors
- Use AWS X-Ray for detailed request tracing
- Enable debug logging in Lambda functions

## Cleanup

To remove all resources and stop charges:

```bash
sam delete --stack-name YOUR-STACK-NAME
```

This will delete:
- All Lambda functions
- API Gateway
- DynamoDB table
- S3 buckets (you may need to empty them first)
- All associated IAM roles and policies

## Local Development

For local testing:

```bash
# Install dependencies
pip install boto3

# Run local API
sam local start-api

# Test locally
curl -X POST http://localhost:3000/classify -d '{"file_base64":"...","filename":"test.jpg"}'
```

## License

This project uses AWS services which have their own pricing and terms. Please review AWS service pricing and terms before deployment.