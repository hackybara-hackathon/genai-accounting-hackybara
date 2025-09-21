# S3 Website Deployment Script
# Usage: .\deploy-website.ps1

param(
    [string]$BucketName = "genai-accounting-website-427566522814",
    [string]$Region = "ap-southeast-1",
    [switch]$DryRun = $false
)

Write-Host "🚀 Starting S3 Website Deployment..." -ForegroundColor Green
Write-Host "📦 Bucket: $BucketName" -ForegroundColor Yellow
Write-Host "🌍 Region: $Region" -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No files will be uploaded" -ForegroundColor Magenta
}

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
    Write-Host "✅ AWS CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Check if bucket exists
try {
    aws s3api head-bucket --bucket $BucketName --region $Region 2>$null
    Write-Host "✅ S3 bucket $BucketName exists" -ForegroundColor Green
} catch {
    Write-Host "❌ S3 bucket $BucketName not found or not accessible" -ForegroundColor Red
    exit 1
}

# Function to sync files with progress
function Sync-ToS3 {
    param($LocalPath, $S3Path, $FileType, $CacheControl = "max-age=300")
    
    Write-Host "📁 Syncing $FileType files..." -ForegroundColor Cyan
    Write-Host "   From: $LocalPath" -ForegroundColor Gray
    Write-Host "   To: s3://$BucketName$S3Path" -ForegroundColor Gray
    
    $syncCommand = "aws s3 sync `"$LocalPath`" `"s3://$BucketName$S3Path`" --cache-control `"$CacheControl`" --delete"
    
    if ($DryRun) {
        $syncCommand += " --dryrun"
    }
    
    Invoke-Expression $syncCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $FileType sync completed" -ForegroundColor Green
    } else {
        Write-Host "❌ $FileType sync failed" -ForegroundColor Red
        return $false
    }
    return $true
}

# Sync HTML files (frontend/layout -> S3 root)
$success = Sync-ToS3 "frontend\layout" "" "HTML" "max-age=300"
if (-not $success) { exit 1 }

# Sync CSS files
$success = Sync-ToS3 "css" "/css" "CSS" "max-age=86400"
if (-not $success) { exit 1 }

# Sync JS files
$success = Sync-ToS3 "frontend\js" "/js" "JavaScript" "max-age=86400"
if (-not $success) { exit 1 }

# Set bucket policy for public access (only if not dry run)
if (-not $DryRun) {
    Write-Host "🔓 Setting public read policy..." -ForegroundColor Cyan
    
    $bucketPolicy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BucketName/*"
        }
    ]
}
"@ | ConvertTo-Json -Compress

    $policyFile = [System.IO.Path]::GetTempFileName()
    $bucketPolicy | Out-File -FilePath $policyFile -Encoding UTF8
    
    try {
        aws s3api put-bucket-policy --bucket $BucketName --policy file://$policyFile
        Write-Host "✅ Bucket policy updated" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Warning: Could not update bucket policy" -ForegroundColor Yellow
    } finally {
        Remove-Item $policyFile -ErrorAction SilentlyContinue
    }
}

# Display completion summary
Write-Host ""
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "🌐 Website URL: http://$BucketName.s3-website-$Region.amazonaws.com" -ForegroundColor Cyan
Write-Host "📊 Cache Settings:" -ForegroundColor Yellow
Write-Host "   • HTML files: 5 minutes (for quick updates)" -ForegroundColor Gray
Write-Host "   • CSS/JS files: 24 hours (for performance)" -ForegroundColor Gray

if ($DryRun) {
    Write-Host ""
    Write-Host "ℹ️ This was a dry run. To actually deploy, run without -DryRun flag" -ForegroundColor Magenta
}