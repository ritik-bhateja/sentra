#!/bin/bash
# Agent deployment to AgentCore Runtime (CLI version)

set -e

# Load infra if you have env vars (optional)

# --- Agent Config ---
# Equivalent to:
# Runtime().configure(entrypoint="main.py", auto_create_execution_role=True, auto_create_ecr=True, ...)

agentcore configure \
    --entrypoint main.py \
    --name Sentra_Agent \
    --region ${REGION:-"ap-south-1"} \
    --execution-role arn:aws:iam::628897991744:role/AmazonBedrockAgentCoreSDKRuntime-ap-south-1-1f8243ecb1 \
    --ecr 628897991744.dkr.ecr.ap-south-1.amazonaws.com/bedrock-agentcore-sentra_agent\
    --requirements-file requirements.txt \
    --non-interactive

# --- Launch Agent ---
agentcore launch --auto-update-on-conflict

echo "Agent deployment complete!"