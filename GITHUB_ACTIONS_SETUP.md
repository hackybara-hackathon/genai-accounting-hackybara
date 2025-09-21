# 🔐 GitHub Actions Setup Guide

## Step 1: Get Your AWS Credentials

You already have AWS CLI configured locally, so let's get your credentials:

```powershell
# Check your current AWS configuration
aws configure list

# Get your AWS account ID
aws sts get-caller-identity
```

## Step 2: Add Secrets to GitHub

1. **Go to your GitHub repository**: https://github.com/hackybara-hackathon/genai-accounting-hackybara

2. **Navigate to Settings**:
   - Click **Settings** tab (at the top of your repo)
   - Click **Secrets and variables** in the left sidebar
   - Click **Actions**

3. **Add these secrets** (click "New repository secret" for each):

   **Secret 1: AWS_ACCESS_KEY_ID**
   - Name: `AWS_ACCESS_KEY_ID`
   - Value: Your AWS Access Key ID (starts with `AKIA...`)

   **Secret 2: AWS_SECRET_ACCESS_KEY**
   - Name: `AWS_SECRET_ACCESS_KEY` 
   - Value: Your AWS Secret Access Key (long string)

## Step 3: Test the Setup

1. **Make a small change** to any file in the `frontend/` folder
2. **Commit and push** to the `main` branch:
   ```bash
   git add .
   git commit -m "test: trigger github actions deployment"
   git push origin main
   ```

3. **Watch the deployment**:
   - Go to the **Actions** tab in your GitHub repo
   - You should see a new workflow run called "🚀 Deploy Frontend to S3"
   - Click on it to see the progress

## Step 4: Manual Deployment

You can also trigger deployments manually:

1. Go to **Actions** tab
2. Click **🚀 Deploy Frontend to S3** 
3. Click **Run workflow**
4. Click the green **Run workflow** button

## 🎯 What Happens Next

Once set up, every time you push changes to:
- `frontend/layout/*.html`
- `frontend/js/*.js`
- `css/*.css`

GitHub Actions will automatically:
1. ✅ Sync your files to S3
2. ✅ Set proper cache headers
3. ✅ Make your website publicly accessible
4. ✅ Show you the deployment results

## 🌐 Your Website URL

After successful deployment, your website will be live at:
**http://genai-accounting-website-427566522814.s3-website-ap-southeast-1.amazonaws.com**

---

## 🆘 Need Help?

**Can't find your AWS credentials?**
```powershell
# Check your AWS credentials file
cat ~/.aws/credentials
```

**Deployment failing?**
- Check the Actions logs in GitHub
- Verify your AWS credentials have S3 permissions
- Make sure your S3 bucket exists

**Want to test locally first?**
```bash
npm run deploy:dry-run  # See what would be deployed
npm run deploy:website  # Deploy manually from your machine
```