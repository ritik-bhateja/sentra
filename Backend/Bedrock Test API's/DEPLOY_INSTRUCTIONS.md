# Lambda Deployment Instructions - Fix "No module named 'bedrock_agentcore'"

## Problem
The Lambda function cannot find the `bedrock_agentcore` module because it's not included in the deployment package.

## Solution
You need to package the dependencies WITH your Lambda function code.

---

## Option 1: Automated Deployment (Recommended)

### Step 1: Make script executable
```bash
cd Backend
chmod +x deploy_lambda.sh
```

### Step 2: Run deployment script
```bash
./deploy_lambda.sh
```

This will:
- Install all dependencies
- Package everything into a ZIP
- Deploy/update your Lambda function
- Clean up temporary files

---

## Option 2: Manual Deployment

### Step 1: Create package directory
```bash
cd Backend
mkdir -p lambda_package
```

### Step 2: Install dependencies
```bash
pip install bedrock-agentcore boto3 -t lambda_package/ --upgrade
```

**Important:** Use `-t lambda_package/` to install INTO the package directory.

### Step 3: Copy Lambda function
```bash
cp lambda_glue_schema_fetcher.py lambda_package/
```

### Step 4: Create ZIP file
```bash
cd lambda_package
zip -r ../lambda_glue_schema_fetcher.zip .
cd ..
```

### Step 5: Update Lambda function
```bash
aws lambda update-function-code \
  --function-name SentraGlueSchemaLoader \
  --zip-file fileb://lambda_glue_schema_fetcher.zip \
  --region ap-south-1
```

### Step 6: Clean up
```bash
rm -rf lambda_package
```

---

## Option 3: Using AWS Console

### Step 1: Create package locally
```bash
cd Backend
mkdir lambda_package
pip install bedrock-agentcore boto3 -t lambda_package/
cp lambda_glue_schema_fetcher.py lambda_package/
cd lambda_package
zip -r ../lambda_glue_schema_fetcher.zip .
cd ..
```

### Step 2: Upload via Console
1. Go to AWS Lambda Console
2. Find your function: `SentraGlueSchemaLoader`
3. Click "Upload from" → ".zip file"
4. Select `lambda_glue_schema_fetcher.zip`
5. Click "Save"

---

## Verification

### Test the function
```bash
aws lambda invoke \
  --function-name SentraGlueSchemaLoader \
  --region ap-south-1 \
  response.json

cat response.json | jq .
```

### Expected Success Response
```json
{
  "statusCode": 200,
  "body": "{\"success\": true, \"memory_id\": \"...\", \"columns\": 142, \"event_count\": 1}"
}
```

### View Logs
```bash
aws logs tail /aws/lambda/SentraGlueSchemaLoader --follow --region ap-south-1
```

Expected log output:
```
🚀 Lambda execution started
📍 STEP 1: Fetch schema from Glue
✅ Fetched 142 columns
...
🎉 SUCCESS! Schema loaded to memory
```

---

## Troubleshooting

### Issue: "No module named 'bedrock_agentcore'"
**Cause:** Dependencies not included in ZIP file.

**Solution:** Make sure you install dependencies INTO the lambda_package directory:
```bash
pip install bedrock-agentcore -t lambda_package/
```

### Issue: ZIP file too large
**Cause:** Too many dependencies or large files.

**Solution:** Use Lambda Layers for large dependencies:
```bash
# Create layer
mkdir python
pip install bedrock-agentcore -t python/
zip -r bedrock-layer.zip python

# Upload layer
aws lambda publish-layer-version \
  --layer-name bedrock-agentcore-layer \
  --zip-file fileb://bedrock-layer.zip \
  --compatible-runtimes python3.11 \
  --region ap-south-1

# Attach layer to function
aws lambda update-function-configuration \
  --function-name SentraGlueSchemaLoader \
  --layers arn:aws:lambda:ap-south-1:628897991744:layer:bedrock-agentcore-layer:1 \
  --region ap-south-1
```

### Issue: Permission denied
**Cause:** IAM role doesn't have required permissions.

**Solution:** Verify IAM role has:
- `glue:GetTable`
- `bedrock:*` (for memory operations)
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

### Issue: Timeout
**Cause:** Function takes too long.

**Solution:** Increase timeout:
```bash
aws lambda update-function-configuration \
  --function-name SentraGlueSchemaLoader \
  --timeout 180 \
  --region ap-south-1
```

---

## Package Structure

Your ZIP file should contain:
```
lambda_glue_schema_fetcher.zip
├── lambda_glue_schema_fetcher.py    # Your function code
├── bedrock_agentcore/               # Dependency
│   ├── __init__.py
│   ├── memory.py
│   └── ...
├── boto3/                           # Dependency (optional, included in Lambda)
└── other dependencies...
```

---

## Quick Commands Reference

```bash
# Full deployment (one command)
cd Backend && chmod +x deploy_lambda.sh && ./deploy_lambda.sh

# Manual deployment
cd Backend
mkdir lambda_package
pip install bedrock-agentcore boto3 -t lambda_package/
cp lambda_glue_schema_fetcher.py lambda_package/
cd lambda_package && zip -r ../lambda_glue_schema_fetcher.zip . && cd ..
aws lambda update-function-code --function-name SentraGlueSchemaLoader --zip-file fileb://lambda_glue_schema_fetcher.zip --region ap-south-1
rm -rf lambda_package

# Test
aws lambda invoke --function-name SentraGlueSchemaLoader --region ap-south-1 response.json && cat response.json | jq .

# View logs
aws logs tail /aws/lambda/SentraGlueSchemaLoader --follow --region ap-south-1
```

---

## Notes

1. **boto3 is included** in Lambda runtime, but including it doesn't hurt
2. **bedrock-agentcore MUST be included** - it's not in Lambda runtime
3. **ZIP from inside lambda_package/** - don't include the parent folder
4. **Test locally first** using `python lambda_glue_schema_fetcher.py`
5. **Check ZIP size** - Lambda has a 50MB limit for direct upload (250MB unzipped)

---

## Support

If you continue to have issues:
1. Check CloudWatch logs for detailed error messages
2. Verify IAM permissions
3. Test dependencies locally: `python -c "from bedrock_agentcore.memory import MemoryClient"`
4. Ensure you're using Python 3.11 runtime
