import os
import sys
from bedrock_agentcore.memory import MemoryClient

# Allow passing actor_id and session_id as command line arguments
ACTOR_ID = sys.argv[1] if len(sys.argv) > 1 else 'schema_loader'
SESSION_ID = sys.argv[2] if len(sys.argv) > 2 else 'insurance_schema_session'
REGION = os.getenv("AWS_REGION", "ap-south-1")

print(f"Viewing memory for:")
print(f"  Actor ID: {ACTOR_ID}")
print(f"  Session ID: {SESSION_ID}")
print()

client = MemoryClient(region_name=REGION)
memory_name = "Sentra_Agent_Memory_V1"
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

# Check what's stored in memory
print("=== Memory Contents ===")
recent_turns = client.get_last_k_turns(
    memory_id=memory_id,
    actor_id=ACTOR_ID,
    session_id=SESSION_ID,
    k=10 # Get last 10 turns
)

if not recent_turns:
    print("No memory found for this actor_id and session_id combination.")
else:
    print(f"Found {len(recent_turns)} conversation turn(s)\n")
    # Reverse to show oldest first (chronological order)
    for i, turn in enumerate(reversed(recent_turns), 1):
        print(f"{'='*70}")
        print(f"Turn {i}:")
        print(f"{'='*70}")
        for message in turn:
            role = message['role']
            content = message['content']['text']
            print(f"\n{role.upper()}:")
            print(f"{content[:500]}..." if len(content) < 500 else content)
        print()