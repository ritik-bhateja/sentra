#!/usr/bin/env python3
"""Test Lambda Glue Schema Fetcher with Memory Loading"""

import json
from lambda_glue_schema_fetcher import lambda_handler

print("🧪 Testing Lambda Function (Glue + Memory)\n")
result = lambda_handler({}, None)

print(f"\n📊 Response Status: {result['statusCode']}")

if result['statusCode'] == 200:
    body = json.loads(result['body'])
    print("\n✅ Success!")
    print(f"   Memory ID: {body.get('memory_id', 'N/A')}")
    print(f"   Actor ID: {body.get('actor_id', 'N/A')}")
    print(f"   Session ID: {body.get('session_id', 'N/A')}")
    print(f"   Columns Loaded: {body.get('columns', 'N/A')}")
    print(f"   Event Count: {body.get('event_count', 'N/A')}")
else:
    print(f"\n❌ Failed: {result['body']}")
