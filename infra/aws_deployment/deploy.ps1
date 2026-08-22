$ErrorActionPreference = "Stop"
$REGION = "us-east-1"
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text).Trim()
$S3_BUCKET = "leasebuddy-uploads-$ACCOUNT_ID"

Write-Host "Starting LeaseBuddy AWS Deployment..." -ForegroundColor Green
Write-Host "Account ID: $ACCOUNT_ID" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan

# 1. Login to ECR
Write-Host "`n[1/6] Authenticating Docker with AWS ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# 2. Create ECR Repositories (Ignore if they already exist)
Write-Host "`n[2/6] Creating ECR Repositories..." -ForegroundColor Yellow
$repos = @("leasebuddy-classify", "leasebuddy-extract", "leasebuddy-chunk")
foreach ($repo in $repos) {
    try {
        aws ecr describe-repositories --repository-names $repo --region $REGION > $null 2>&1
    } catch {
        aws ecr create-repository --repository-name $repo --region $REGION > $null
        Write-Host "Created repository: $repo"
    }
}

# 3. Build and Push Lambda Images
Write-Host "`n[3/6] Building and pushing Docker images (This may take a few minutes)..." -ForegroundColor Yellow

$lambdas = @{
    "leasebuddy-classify" = "lambdas\classify";
    "leasebuddy-extract" = "lambdas\extract";
    "leasebuddy-chunk" = "lambdas\chunk_embed"
}

foreach ($lambda in $lambdas.GetEnumerator()) {
    $repoName = $lambda.Key
    $path = $lambda.Value
    $imageUri = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/${repoName}:latest"
    
    Write-Host "Building $repoName..."
    docker build --platform linux/amd64 --provenance=false -t $imageUri "C:\Users\ianjh\Desktop\LeaseBuddy\$path"
    Write-Host "Pushing $repoName..."
    docker push $imageUri
}

# 4. Create IAM Role for Lambdas
Write-Host "`n[4/6] Setting up IAM Roles..." -ForegroundColor Yellow
$roleName = "LeaseBuddyLambdaExecutionRole"
$trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@
Set-Content -Path "C:\Users\ianjh\Desktop\LeaseBuddy\infra\aws_deployment\trust-policy.json" -Value $trustPolicy

try {
    aws iam get-role --role-name $roleName > $null 2>&1
} catch {
    aws iam create-role --role-name $roleName --assume-role-policy-document file://C:\Users\ianjh\Desktop\LeaseBuddy\infra\aws_deployment\trust-policy.json > $null
    Write-Host "Created IAM Role: $roleName"
    Start-Sleep -Seconds 10 # Wait for role to propagate
}

# Attach basic execution policy
aws iam attach-role-policy --role-name $roleName --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
# Attach custom policy from existing file
aws iam put-role-policy --role-name $roleName --policy-name LeaseBuddyCustomPolicy --policy-document file://C:\Users\ianjh\Desktop\LeaseBuddy\infra\aws\lambda-iam-role.json

# 5. Create Lambda Functions
Write-Host "`n[5/6] Creating AWS Lambda Functions..." -ForegroundColor Yellow
$roleArn = "arn:aws:iam::${ACCOUNT_ID}:role/${roleName}"

foreach ($lambda in $lambdas.GetEnumerator()) {
    $repoName = $lambda.Key
    $functionName = $repoName # e.g. leasebuddy-classify
    $imageUri = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/${repoName}:latest"
    
    try {
        aws lambda get-function --function-name $functionName > $null 2>&1
        Write-Host "Updating existing function $functionName..."
        aws lambda update-function-code --function-name $functionName --image-uri $imageUri > $null
    } catch {
        Write-Host "Creating function $functionName..."
        aws lambda create-function `
            --function-name $functionName `
            --package-type Image `
            --code ImageUri=$imageUri `
            --role $roleArn `
            --timeout 60 `
            --memory-size 512 > $null
    }
}

# 6. Create S3 Bucket
Write-Host "`n[6/6] Creating S3 Bucket..." -ForegroundColor Yellow
try {
    aws s3api head-bucket --bucket $S3_BUCKET > $null 2>&1
    Write-Host "S3 bucket $S3_BUCKET already exists."
} catch {
    aws s3api create-bucket --bucket $S3_BUCKET --region $REGION > $null
    Write-Host "Created S3 bucket: $S3_BUCKET"
}

Write-Host "`nDeployment Script Completed Successfully!" -ForegroundColor Green
