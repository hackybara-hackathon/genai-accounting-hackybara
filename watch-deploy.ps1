# Development Watch Script - Auto-deploy on file changes
# Usage: .\watch-deploy.ps1

param(
    [string]$BucketName = "genai-accounting-website-427566522814",
    [int]$WatchInterval = 5
)

Write-Host "👀 Starting file watcher for auto-deployment..." -ForegroundColor Green
Write-Host "📦 Bucket: $BucketName" -ForegroundColor Yellow
Write-Host "⏱️ Check interval: $WatchInterval seconds" -ForegroundColor Yellow
Write-Host "📁 Watching: frontend/, css/, js/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop watching" -ForegroundColor Magenta
Write-Host ""

# Paths to watch
$watchPaths = @(
    "frontend\layout\*.html",
    "frontend\js\*.js", 
    "css\*.css"
)

# Store last write times
$lastWriteTimes = @{}

# Initialize last write times
foreach ($path in $watchPaths) {
    Get-ChildItem $path -ErrorAction SilentlyContinue | ForEach-Object {
        $lastWriteTimes[$_.FullName] = $_.LastWriteTime
    }
}

Write-Host "✅ Initial scan completed - watching for changes..." -ForegroundColor Green

# Function to deploy changed files
function Deploy-ChangedFiles {
    param($ChangedFiles)
    
    Write-Host ""
    Write-Host "🔄 Changes detected in:" -ForegroundColor Yellow
    $ChangedFiles | ForEach-Object { Write-Host "   • $_" -ForegroundColor Gray }
    
    Write-Host "🚀 Starting incremental deployment..." -ForegroundColor Cyan
    
    # Determine which folders to sync based on changed files
    $syncHTML = $false
    $syncJS = $false
    $syncCSS = $false
    
    foreach ($file in $ChangedFiles) {
        if ($file -like "*\frontend\layout\*") { $syncHTML = $true }
        if ($file -like "*\frontend\js\*") { $syncJS = $true }
        if ($file -like "*\css\*") { $syncCSS = $true }
    }
    
    # Sync only changed file types
    if ($syncHTML) {
        Write-Host "📄 Syncing HTML files..." -ForegroundColor Cyan
        aws s3 sync "frontend\layout" "s3://$BucketName/" --include "*.html" --cache-control "max-age=300"
    }
    
    if ($syncJS) {
        Write-Host "📜 Syncing JavaScript files..." -ForegroundColor Cyan
        aws s3 sync "frontend\js" "s3://$BucketName/js/" --include "*.js" --cache-control "max-age=86400"
    }
    
    if ($syncCSS) {
        Write-Host "🎨 Syncing CSS files..." -ForegroundColor Cyan
        aws s3 sync "css" "s3://$BucketName/css/" --include "*.css" --cache-control "max-age=86400"
    }
    
    Write-Host "✅ Deployment completed!" -ForegroundColor Green
    Write-Host "🌐 Website: http://$BucketName.s3-website-ap-southeast-1.amazonaws.com" -ForegroundColor Cyan
    Write-Host ""
}

# Main watch loop
try {
    while ($true) {
        $changedFiles = @()
        
        # Check each watched path for changes
        foreach ($path in $watchPaths) {
            Get-ChildItem $path -ErrorAction SilentlyContinue | ForEach-Object {
                $currentWriteTime = $_.LastWriteTime
                $lastWriteTime = $lastWriteTimes[$_.FullName]
                
                if (-not $lastWriteTime -or $currentWriteTime -gt $lastWriteTime) {
                    $changedFiles += $_.FullName
                    $lastWriteTimes[$_.FullName] = $currentWriteTime
                }
            }
        }
        
        # Deploy if changes detected
        if ($changedFiles.Count -gt 0) {
            Deploy-ChangedFiles $changedFiles
        }
        
        # Wait before next check
        Start-Sleep -Seconds $WatchInterval
    }
} catch {
    Write-Host ""
    Write-Host "👋 File watcher stopped" -ForegroundColor Yellow
}