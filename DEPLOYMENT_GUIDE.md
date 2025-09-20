# Complete AWS Deployment Guide

This guide walks you through the complete setup and deployment of your GenAI Accounting System from scratch.

## 🔧 **Pre-Deployment AWS Configuration**

### 1. **AWS Account Setup**

#### Required AWS Services
- ✅ AWS Lambda (serverless functions)
- ✅ Amazon API Gateway (REST API)
- ✅ Amazon S3 (file storage + website hosting)
- ✅ Amazon RDS PostgreSQL (database)
- ✅ Amazon Bedrock (AI models)
- ✅ AWS SAM CLI (deployment tool)

#### Cost Estimate
- **Development/Testing**: $10-30/month
- **Small Business**: $50-100/month
- **Medium Business**: $100-300/month

### 2. **Enable Amazon Bedrock Model Access** ⚠️ **CRITICAL FIRST STEP**

Before deployment, you MUST enable model access in Bedrock:

1. **Go to AWS Bedrock Console**
   - Navigate to: https://console.aws.amazon.com/bedrock/
   - Choose your region (recommended: `us-east-1` or `ap-southeast-1`)

2. **Enable Model Access**
   - Click "Model access" in the left sidebar
   - Click "Request model access" button
   - Enable access for these model providers:
     - ✅ **Meta** (for Llama models) - ⭐ RECOMMENDED
     - ✅ **Mistral AI** (for Mistral models)
     - ✅ **Amazon** (for Nova models)
     - ✅ **Anthropic** (for Claude models)

3. **Submit Request**
   - Click "Request model access"
   - **Wait 5-15 minutes** for approval (usually instant)
   - Refresh page to confirm "Access granted" status

> ⚠️ **Important**: Without model access, your deployment will succeed but receipt classification will fail!

### 3. **Create PostgreSQL Database**

#### Option A: Amazon RDS (Recommended for Production)

1. **Go to RDS Console**
   - Navigate to: https://console.aws.amazon.com/rds/

2. **Create Database**
   - Click "Create database"
   - Choose "Standard create"
   - Engine: **PostgreSQL**
   - Version: **PostgreSQL 15** or later
   - Template: **Free tier** (for testing) or **Production**

3. **Database Configuration**
   ```
   DB Instance Identifier: genai-accounting-db
   Master Username: accounting_admin
   Master Password: [Create strong password - SAVE THIS!]
   DB Name: accounting
   ```

4. **Instance Configuration**
   - Instance class: `db.t3.micro` (free tier) or `db.t3.small`
   - Storage: 20 GB General Purpose SSD
   - Enable storage autoscaling: Yes

5. **Connectivity**
   - Public access: **Yes** (for initial setup)
   - VPC security group: Create new or use default
   - Database port: 5432

6. **Additional Configuration**
   - Initial database name: `accounting`
   - Enable automated backups: Yes
   - Backup retention: 7 days

7. **Create Database**
   - Click "Create database"
   - **Wait 10-15 minutes** for creation
   - Note down the **Endpoint** (you'll need this for deployment)

8. **Security Group Configuration**
   - Go to EC2 → Security Groups
   - Find your RDS security group
   - Add inbound rule:
     - Type: PostgreSQL
     - Port: 5432
     - Source: 0.0.0.0/0 (for initial setup - restrict later)

#### Option B: Local PostgreSQL (Development Only)
```bash
# Install PostgreSQL locally
# Windows: Download from postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql
```

### 4. **Set Up Database Schema**

1. **Connect to Database**
   ```bash
   # Using psql command line
   psql -h YOUR-RDS-ENDPOINT -U accounting_admin -d accounting
   
   # Or use pgAdmin, DBeaver, or any PostgreSQL client
   ```

2. **Create Database Schema**
   ```sql
   -- Run the complete database.sql file
   -- Located at: database/database.sql in your project
   ```

3. **Create Initial Organization**
   ```sql
   -- Create your organization
   INSERT INTO organizations (id, name) 
   VALUES (gen_random_uuid(), 'Your Company Name');
   
   -- Note down the organization ID - you'll need it for deployment
   SELECT id, name FROM organizations;
   ```

### 5. **Install Required Tools**

#### AWS CLI
```bash
# Windows (using AWS CLI installer)
# Download from: https://aws.amazon.com/cli/

# Verify installation
aws --version
```

#### AWS SAM CLI
```bash
# Windows (using MSI installer)
# Download from: https://aws.amazon.com/serverless/sam/

# Verify installation
sam --version
```

#### Configure AWS CLI
```bash
aws configure
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]  
# Default region name: us-east-1 (or ap-southeast-1)
# Default output format: json
```

## 🚀 **Deployment Steps**

### Step 1: Prepare Your Project

1. **Clone/Download Your Project**
   ```bash
   cd c:\Users\user\OneDrive\Desktop\genai-accounting-hackybara
   ```

2. **Verify Project Structure**
   ```
   ├── src/
   │   ├── handlers.py
   │   ├── db.py
   │   ├── bedrock_client.py
   │   └── parsers.py
   ├── frontend/
   │   ├── layout/
   │   └── js/
   ├── template.yaml
   ├── requirements.txt
   └── database/
       └── database.sql
   ```

### Step 2: Choose Your AI Model

Run the interactive deployment script:
```bash
# Make script executable
chmod +x deploy-with-model.sh

# Run deployment script
./deploy-with-model.sh
```

Or choose manually:
- **Small Business**: `meta.llama3-2-3b-instruct-v1:0` (default)
- **Medium Business**: `mistral.mistral-7b-instruct-v0:2`  
- **High Accuracy**: `meta.llama3-2-11b-instruct-v1:0`

### Step 3: Deploy Backend Infrastructure

```bash
# Build the application
sam build

# Deploy with guided setup (first time)
sam deploy --guided
```

#### Deployment Configuration Prompts:

```
Stack Name [genai-accounting]: genai-accounting
AWS Region [us-east-1]: us-east-1
Parameter WebsiteBucketName [genai-accounting-website]: your-website-bucket
Parameter ReceiptsBucketName [genai-accounting-receipts]: your-receipts-bucket
Parameter ModelId [meta.llama3-2-3b-instruct-v1:0]: [Press Enter or choose model]
Parameter OrganizationId []: [Paste your organization UUID from database]
Parameter DatabaseHost []: [Your RDS endpoint]
Parameter DatabasePort [5432]: 5432
Parameter DatabaseName [accounting]: accounting
Parameter DatabaseUser []: accounting_admin
Parameter DatabasePassword []: [Your database password]
Confirm changes before deploy [Y/n]: Y
Allow SAM CLI IAM role creation [Y/n]: Y
Disable rollback [y/N]: N
ClassifyFunction may not have authorization defined, Is this okay? [y/N]: Y
Save parameters to configuration file [Y/n]: Y
SAM configuration file [samconfig.toml]: [Press Enter]
SAM configuration environment [default]: [Press Enter]
```

### Step 4: Deploy Frontend

1. **Get API Gateway URL**
   - After deployment, note the `ApiUrl` in the outputs
   - Example: `https://abcd1234.execute-api.us-east-1.amazonaws.com/prod`

2. **Update Frontend Configuration**
   - Edit `frontend/js/config.js`
   - Update the `PRODUCTION_API_URL` with your API Gateway URL:
   ```javascript
   const PRODUCTION_API_URL = 'https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod';
   ```

3. **Upload Frontend to S3**
   ```bash
   # Get your website bucket name from deployment outputs
   aws s3 sync frontend/ s3://your-website-bucket-name-ACCOUNT-ID/ --delete
   ```

4. **Get Website URL**
   - From deployment outputs: `WebsiteUrl`
   - Example: `http://your-website-bucket-name-123456789.s3-website-us-east-1.amazonaws.com`

### Step 5: Test Your Deployment

1. **Test API Endpoints**
   ```bash
   # Test summary endpoint
   curl https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/summary
   
   # Test transactions endpoint
   curl https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/transactions
   ```

2. **Test Frontend**
   - Open your website URL in browser
   - Try uploading a receipt
   - Check dashboard for data
   - View transactions page

3. **Check CloudWatch Logs**
   - Go to CloudWatch → Log groups
   - Look for `/aws/lambda/genai-accounting-*` log groups
   - Check for any errors

## 🔍 **Troubleshooting Common Issues**

### Issue 1: "Model access denied"
**Solution**: Enable model access in Bedrock console (Step 2 above)

### Issue 2: "Database connection failed"
**Solution**: 
- Check RDS security group allows port 5432
- Verify database endpoint and credentials
- Ensure database is publicly accessible (initially)

### Issue 3: "CORS errors in frontend"
**Solution**: 
- Verify API Gateway has CORS enabled
- Check frontend is calling correct API URL

### Issue 4: "Receipt upload fails"
**Solution**:
- Check S3 bucket permissions
- Verify Bedrock model access
- Check Lambda function logs

### Issue 5: "Frontend shows 'Development Mode'"
**Solution**:
- Update `PRODUCTION_API_URL` in `config.js`
- Re-upload frontend files to S3

## 🔒 **Security Hardening (After Testing)**

1. **Database Security**
   - Restrict RDS security group to Lambda subnets only
   - Disable public access to RDS
   - Use VPC endpoints

2. **S3 Security**
   - Enable bucket versioning
   - Enable server-side encryption
   - Set up bucket policies

3. **API Gateway**
   - Add API keys for production
   - Set up throttling limits
   - Enable request logging

## 📊 **Monitoring & Maintenance**

1. **Set Up CloudWatch Alarms**
   - Lambda errors
   - API Gateway 4xx/5xx errors
   - Database connections

2. **Cost Monitoring**
   - Set up billing alarms
   - Monitor Bedrock model usage
   - Track S3 storage costs

3. **Backup Strategy**
   - RDS automated backups (enabled by default)
   - S3 cross-region replication for receipts
   - Export CloudWatch logs

## 🎯 **Next Steps After Deployment**

1. **Add Custom Domain** (Optional)
   - Register domain in Route 53
   - Set up CloudFront distribution
   - Configure SSL certificate

2. **Set Up Development Environment**
   - Create separate dev stack
   - Use different database
   - Test new features safely

3. **Add More Features**
   - User authentication
   - Multi-tenant support
   - Advanced reporting
   - Mobile app integration

## 📞 **Support**

If you encounter issues:
1. Check CloudWatch logs first
2. Verify all AWS services are in the same region
3. Confirm model access in Bedrock
4. Test database connectivity separately

---

**Total Deployment Time**: 30-60 minutes (including RDS creation time)
**Estimated Cost**: $10-30/month for small business usage