# 🚀 GenAI Accounting - Complete Deployment Guide

## Current Architecture ✅
- **Frontend**: S3 Static Website (Automated via GitHub Actions)
- **Backend**: AWS Lambda Functions 
- **Database**: PostgreSQL on AWS RDS
- **AI**: AWS Bedrock (Llama 3.2)
- **Storage**: S3 for receipts

---

# 🌐 Frontend Deployment (S3 + GitHub Actions)

## 🔧 Setup Instructions

### 1. Configure GitHub Secrets

You need to add AWS credentials to your GitHub repository:

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key ID | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |

### 2. AWS IAM Permissions

Your AWS user needs the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject", 
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:PutBucketPolicy",
                "s3:GetBucketPolicy"
            ],
            "Resource": [
                "arn:aws:s3:::genai-accounting-website-427566522814",
                "arn:aws:s3:::genai-accounting-website-427566522814/*"
            ]
        }
    ]
}
```

## 🎯 How Automated Deployment Works

### Automatic Deployment
- **Triggers**: Pushes to `main` branch with changes in:
  - `frontend/` folder
  - `css/` folder  
  - `js/` folder
  - Workflow file itself

### Manual Deployment
- Go to **Actions** tab in GitHub
- Click **🚀 Deploy Frontend to S3**
- Click **Run workflow**

### What Gets Deployed
- **HTML files**: `frontend/layout/` → S3 root
- **CSS files**: `css/` → `s3://bucket/css/`
- **JS files**: `frontend/js/` → `s3://bucket/js/`

### Cache Settings
- **HTML files**: 5 minutes (for quick content updates)
- **CSS/JS files**: 24 hours (for performance)

## 🌐 Website URLs

After deployment, your website will be available at:
- **Production**: http://genai-accounting-website-427566522814.s3-website-ap-southeast-1.amazonaws.com

## 📊 Monitoring Deployments

1. Go to **Actions** tab in your GitHub repository
2. Click on any deployment run to see:
   - ✅ Success/failure status
   - 📝 Detailed logs
   - ⏱️ Deployment time
   - 📊 Files synced count

---

# ⚡ Backend Deployment (AWS Lambda + SAM)

## Current Backend Status ✅
- **API Gateway**: https://xfnv4mgb64.execute-api.ap-southeast-1.amazonaws.com/prod
- **Lambda Functions**: 13 functions deployed
- **Database**: PostgreSQL RDS connected
- **AI Models**: Bedrock Llama 3.2 configured

## Deploy Backend Changes

```bash
# Build and deploy all Lambda functions
sam build && sam deploy

# Deploy with different parameters
sam deploy --parameter-overrides ModelId=meta.llama3-2-11b-instruct-v1:0
```

---

# 🔧 Local Development Commands

```bash
# Test what would be deployed (dry run)
npm run deploy:dry-run

# Deploy frontend manually from local machine  
npm run deploy:website

# Full deployment (SAM + Website)
npm run deploy:full

# Watch for changes and auto-deploy (development)
.\watch-deploy.ps1
```

## 🛠️ Troubleshooting

### Frontend Issues

**❌ AWS credentials error**
- Check your GitHub secrets are correctly set
- Verify AWS user has S3 permissions

**❌ Bucket not found**  
- Ensure your S3 bucket exists: `genai-accounting-website-427566522814`
- Check bucket name matches workflow configuration

**❌ Files not updating**
- Clear browser cache
- Check cache-control headers in S3

### Backend Issues

**❌ Lambda function errors**
- Check CloudWatch logs: `/aws/lambda/genai-accounting-simple-*`
- Verify database connection
- Check environment variables

### Debug Steps

1. Check the Actions logs for detailed error messages
2. Verify S3 bucket permissions in AWS Console
3. Test AWS CLI access locally:
   ```bash
   aws s3 ls s3://genai-accounting-website-427566522814
   ```

---

## 🎉 Benefits of This Setup

✅ **Fully Serverless** - No servers to manage  
✅ **Auto-scaling** - Handles traffic spikes automatically  
✅ **Cost-effective** - Pay only for what you use  
✅ **Highly Available** - Multi-AZ deployment  
✅ **Secure** - IAM roles, encrypted secrets  
✅ **Fast** - CDN-ready, optimized caching