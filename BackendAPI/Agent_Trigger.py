from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
import json
import botocore
import uvicorn

app = FastAPI(title="Sentra Insurance API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Pydantic models for request validation
class QueryRequest(BaseModel):
    user_query: str
    user_id: str
    session_id: str
    user_email: str = None  # Optional, defaults to user_id if not provided

# --------------------------------------------
#  QUERY ENDPOINT — BEDROCK AGENTCORE
# --------------------------------------------
@app.post("/query")
async def send_to_bknd(request: QueryRequest):
    config = botocore.config.Config(
        read_timeout=180,
        connect_timeout=10,
        retries={'max_attempts': 0}
    )

    print(f"Received request: {request.dict()}")
    
    # Validate user_id presence
    if not request.user_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_actor_id",
                "message": "user_id is required"
            }
        )
    
    # Validate session_id presence
    if not request.session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_session_id",
                "message": "session_id is required"
            }
        )
    
    client = boto3.client('bedrock-agentcore', region_name='ap-south-1', config=config)
    
    # Use user_email if provided, otherwise fallback to user_id
    user_email = request.user_email if request.user_email else request.user_id
    
    bknd_payload = json.dumps({
        "user_query": request.user_query,
        "user_id": request.user_id,
        "session_id": request.session_id,
        "user_email": user_email
    })

    try:
        # Use session_id as runtimeSessionId for proper session isolation
        # Frontend generates 33-character session IDs to meet AWS Bedrock requirement
        response = client.invoke_agent_runtime(
            agentRuntimeArn='arn:aws:bedrock-agentcore:ap-south-1:628897991744:runtime/Sentra_Agent-vtVCPEFWbx',
            runtimeSessionId=request.session_id,
            payload=bknd_payload,
            qualifier="DEFAULT"
        )
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        print("Agent Response:", response_data)
        return response_data
    except Exception as e:
        print(f"Error calling Bedrock AgentCore: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "bedrock_error",
                "message": f"Failed to process request: {str(e)}"
            }
        )


# --------------------------------------------
#  HEALTH CHECK ENDPOINT
# --------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Sentra Insurance API"}

# --------------------------------------------
#  RUN SERVER
# --------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
