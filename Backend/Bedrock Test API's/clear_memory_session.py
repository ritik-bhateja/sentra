#!/usr/bin/env python3
"""
Clear Memory Session for Sentra AgentCore Memory

This script provides a simple way to clear/reset memory data for a specific session
by creating a new session ID, effectively isolating the old data.
"""

import os
import sys
import logging
from bedrock_agentcore.memory import MemoryClient
from datetime import datetime
import random
import string

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
REGION = os.getenv("AWS_REGION", "ap-south-1")
MEMORY_NAME = "Sentra_Agent_Memory_V1"
ACTOR_ID = "Sample"
OLD_SESSION_ID = "sample_session"

def generate_new_session_id():
    """Generate a new session ID"""
    timestamp = int(datetime.now().timestamp())
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"sample_session_new_{timestamp}_{random_suffix}"

def initialize_memory_client():
    """Initialize the memory client and get memory_id"""
    try:
        client = MemoryClient(region_name=REGION)
        logger.info(f"✅ Memory client initialized for region: {REGION}")
        
        # Find existing memory
        memories = client.list_memories()
        existing = next((m for m in memories if m["id"].startswith(MEMORY_NAME)), None)
        
        if existing:
            memory_id = existing["id"]
            logger.info(f"📚 Found existing memory: {memory_id}")
            return client, memory_id
        else:
            logger.error(f"❌ Memory '{MEMORY_NAME}' not found")
            return None, None
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize memory client: {e}")
        raise

def check_old_session_data(client, memory_id):
    """Check data in the old session"""
    logger.info(f"🔍 Checking data in old session: {OLD_SESSION_ID}")
    
    try:
        recent_turns = client.get_last_k_turns(
            memory_id=memory_id,
            actor_id=ACTOR_ID,
            session_id=OLD_SESSION_ID,
            k=10
        )
        
        if not recent_turns:
            logger.info("ℹ️ No data found in old session")
            return 0
        
        total_messages = sum(len(turn) for turn in recent_turns)
        logger.info(f"📊 Found {len(recent_turns)} turns with {total_messages} messages in old session")
        
        return len(recent_turns)
        
    except Exception as e:
        logger.error(f"❌ Failed to check old session data: {e}")
        return 0

def create_fresh_session(client, memory_id, new_session_id):
    """Create a fresh session with a clear marker"""
    logger.info(f"🆕 Creating fresh session: {new_session_id}")
    
    try:
        # Create a session start marker
        client.create_event(
            memory_id=memory_id,
            actor_id=ACTOR_ID,
            session_id=new_session_id,
            messages=[("SESSION_STARTED: Fresh session created", "OTHER")]
        )
        
        logger.info("✅ Fresh session created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create fresh session: {e}")
        return False

def verify_fresh_session(client, memory_id, new_session_id):
    """Verify the fresh session is working"""
    logger.info(f"🔍 Verifying fresh session: {new_session_id}")
    
    try:
        recent_turns = client.get_last_k_turns(
            memory_id=memory_id,
            actor_id=ACTOR_ID,
            session_id=new_session_id,
            k=5
        )
        
        if recent_turns and len(recent_turns) == 1:
            logger.info("✅ Fresh session verified - contains only the session start marker")
            return True
        else:
            logger.warning(f"⚠️ Unexpected data in fresh session: {len(recent_turns) if recent_turns else 0} turns")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to verify fresh session: {e}")
        return False

def main():
    """Main function to clear session memory"""
    logger.info("🚀 Starting Sentra AgentCore Memory Session Clear")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Initialize memory client
        client, memory_id = initialize_memory_client()
        
        if not client or not memory_id:
            logger.error("❌ Failed to initialize memory client")
            sys.exit(1)
        
        # Check old session data
        old_data_count = check_old_session_data(client, memory_id)
        
        # Generate new session ID
        new_session_id = generate_new_session_id()
        logger.info(f"🆔 Generated new session ID: {new_session_id}")
        
        # Create fresh session
        if create_fresh_session(client, memory_id, new_session_id):
            # Verify fresh session
            if verify_fresh_session(client, memory_id, new_session_id):
                logger.info("🎉 Memory session cleared successfully!")
                logger.info("=" * 60)
                logger.info("📋 SUMMARY:")
                logger.info(f"   Old Session ID: {OLD_SESSION_ID} ({old_data_count} turns)")
                logger.info(f"   New Session ID: {new_session_id} (fresh)")
                logger.info("=" * 60)
                logger.info("💡 NEXT STEPS:")
                logger.info(f"   1. Update your code to use new session_id: '{new_session_id}'")
                logger.info(f"   2. Or update load_sample_memory.py to use the new session ID")
                logger.info(f"   3. The old session data remains isolated and won't interfere")
                logger.info("=" * 60)
                
                # Create a config file with the new session ID
                config_content = f"""# New Session Configuration
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ACTOR_ID = "Sample"
OLD_SESSION_ID = "{OLD_SESSION_ID}"
NEW_SESSION_ID = "{new_session_id}"

# Use NEW_SESSION_ID in your SQLQueryExecutor initialization:
# executor = SQLQueryExecutor(actor_id=ACTOR_ID, session_id=NEW_SESSION_ID)
"""
                
                with open("Backend/new_session_config.py", "w") as f:
                    f.write(config_content)
                
                logger.info("📄 Created Backend/new_session_config.py with new session details")
                
            else:
                logger.error("❌ Failed to verify fresh session")
                sys.exit(1)
        else:
            logger.error("❌ Failed to create fresh session")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()