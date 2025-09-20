# AWS Configuration Checklist

## ✅ **Pre-Deployment Checklist**

### AWS Account & Tools
- [ ] AWS account with billing configured
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] AWS SAM CLI installed (`sam --version`)
- [ ] Appropriate IAM permissions for deployment

### Amazon Bedrock (⚠️ CRITICAL FIRST!)
- [ ] Navigate to AWS Bedrock console
- [ ] Choose region: `us-east-1` (recommended) or `ap-southeast-1`
- [ ] Go to "Model access" in left sidebar
- [ ] Request access for:
  - [ ] **Meta** (Llama models) ⭐ 
  - [ ] **Mistral AI** (Mistral models)
  - [ ] **Amazon** (Nova models)
  - [ ] **Anthropic** (Claude models)
- [ ] Wait for approval (5-15 minutes)
- [ ] Confirm "Access granted" status

### PostgreSQL Database Setup
- [ ] Create RDS PostgreSQL instance
  - Instance: `db.t3.micro` or larger
  - Username: `accounting_admin`
  - Database name: `accounting`
  - Public access: **Yes** (initially)
- [ ] Note RDS endpoint hostname
- [ ] Configure security group (port 5432 open)
- [ ] Run database schema from `database/database.sql`
- [ ] Create organization record and note UUID

### Information to Gather
- [ ] RDS endpoint: `_________________________`
- [ ] Database password: `_____________________`
- [ ] Organization UUID: `_____________________`
- [ ] Chosen AI model: `_______________________`
- [ ] AWS region: `____________________________`

## 🚀 **Deployment Steps**

### 1. Backend Deployment
```bash
# In your project directory
sam build
sam deploy --guided
```

### 2. Frontend Configuration
- [ ] Update `frontend/js/config.js` with API Gateway URL
- [ ] Upload frontend files to S3 website bucket

### 3. Testing
- [ ] Test API endpoints with curl
- [ ] Open website and test receipt upload
- [ ] Check CloudWatch logs for errors

## ⚠️ **Common Mistakes to Avoid**

1. **Forgetting Bedrock Model Access** - #1 cause of deployment issues
2. **Wrong AWS Region** - Bedrock models vary by region
3. **Database Connection Issues** - Check security groups and credentials
4. **Frontend API URL** - Must update config.js with actual API Gateway URL
5. **Organization UUID** - Must exist in database before deployment

## 🔧 **Quick Commands**

```bash
# Check AWS CLI configuration
aws sts get-caller-identity

# Check SAM CLI
sam --version

# Test database connection
psql -h YOUR-RDS-ENDPOINT -U accounting_admin -d accounting

# Build and deploy
sam build && sam deploy

# Upload frontend
aws s3 sync frontend/ s3://YOUR-BUCKET-NAME/ --delete
```

## 📞 **If Something Goes Wrong**

1. **Check CloudWatch Logs**: AWS Console → CloudWatch → Log groups
2. **Verify Bedrock Access**: AWS Console → Bedrock → Model access
3. **Test Database**: Use psql or database client to connect
4. **Check Region**: All services should be in same region
5. **Review IAM Permissions**: Ensure deployment user has necessary permissions

---

**Estimated Total Time**: 30-60 minutes
**Most Time-Consuming**: RDS creation (10-15 minutes) and Bedrock approval (5-15 minutes)