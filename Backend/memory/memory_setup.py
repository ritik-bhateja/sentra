import os
from bedrock_agentcore.memory import MemoryClient

REGION = os.getenv("AWS_REGION", "ap-south-1")

client = MemoryClient(region_name=REGION)
memory_name = "Sentra_Agent_Memory_V1"  # Match the name from Agent_CICD.py
memory_id = None

memories = client.list_memories()
existing = next((m for m in memories if m["id"].startswith(memory_name)), None)

if existing:
    memory_id = existing["id"]
else:
    memory = client.create_memory_and_wait(
        name=memory_name,
        strategies=[],
        description="Short-term memory for Sentra agent",
        event_expiry_days=7,
    )
    memory_id = memory["id"]
