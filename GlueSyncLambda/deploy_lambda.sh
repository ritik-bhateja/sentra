#!/bin/bash
# Simple Lambda Deployment

FUNCTION_NAME="SentraGlueSchemaLoader"
REGION="ap-south-1"

echo "🚀 Deploying..."

# Clean
rm -rf lambda_package *.zip

# Package
mkdir lambda_package
pip install bedrock-agentcore --platform manylinux2014_x86_64 --target lambda_package/ --python-version 3.11 --only-binary=:all:
cp lambda_glue_schema_fetcher.py lambda_package/
cd lambda_package && zip -r ../lambda.zip . -q && cd ..

# Deploy
aws lambda update-function-code --function-name $FUNCTION_NAME --zip-file fileb://lambda.zip --region $REGION

# Test
aws lambda invoke --function-name $FUNCTION_NAME --region $REGION response.json
cat response.json

# Clean
rm -rf lambda_package

echo "✅ Done!"
