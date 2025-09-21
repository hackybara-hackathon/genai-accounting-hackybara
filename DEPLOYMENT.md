# GenAI Accounting - Deployment Guide

## Current Status ✅
- **Lambda Functions**: Already deployed to AWS
- **Database**: PostgreSQL on AWS RDS
- **Node.js Backend**: Running locally (needs deployment)

## Quick Deployment Options

### Option 1: AWS Elastic Beanstalk (Recommended)

1. **Install AWS CLI and EB CLI:**
   ```bash
   pip install awsebcli
   ```

2. **Initialize and Deploy:**
   ```bash
   eb init
   eb create genai-accounting-app
   eb deploy
   ```

### Option 2: Heroku (Fastest)

1. **Install Heroku CLI**
2. **Deploy:**
   ```bash
   heroku create genai-accounting-app
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

### Option 3: Railway (Modern)

1. **Connect to Railway**: https://railway.app
2. **Import from GitHub**
3. **Auto-deploy**

## Environment Variables Needed

```
DATABASE_HOST=hackybara-accounting.cteao02mo068.ap-southeast-1.rds.amazonaws.com
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=hackybara4321
PORT=5000
```

## Post-Deployment Steps

1. **Update frontend config** (`frontend/js/config.js`) with production URLs
2. **Test authentication flow**
3. **Test Lambda integration**

## Architecture After Deployment

```
Users → Load Balancer → Node.js App (Authentication) → Lambda Functions → Database
```

The Node.js app handles:
- User authentication
- Session management 
- Static file serving
- API routing to Lambda functions

Lambda functions handle:
- Receipt processing
- AI classification
- Heavy computations