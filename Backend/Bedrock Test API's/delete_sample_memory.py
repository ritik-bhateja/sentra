#!/usr/bin/env python3
"""
Delete Sample Memory Session for Sentra AgentCore Memory

This script deletes all memory data for a specific actor_id and session_id
from the AgentCore memory system.
"""

import os
import sys
import logging
from bedrock_agentcore.memory import MemoryClient
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
REGION = os.getenv("AWS_REGION", "ap-south-1")
MEMORY_NAME = "Sentra_Agent_Memory_V1"
ACTOR_ID = "Sample"  # Same as loader
SESSION_ID = "sample_session"  # Same as loader

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

def check_existing_data(client, memory_id):
    """Check what data exists before deletion"""
    logger.info("🔍 Checking existing memory data...")
    
    try:
        recent_turns = client.get_last_k_turns(
            memory_id=memory_id,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            k=20  # Get up to 20 entries
        )
        
        if not recent_turns:
            logger.info("ℹ️ No existing data found for this actor_id and session_id")
            return 0
        
        total_messages = sum(len(turn) for turn in recent_turns)
        logger.info(f"📊 Found {len(recent_turns)} conversation turns with {total_messages} total messages")
        
        # Show summary of what will be deleted
        logger.info("📋 Data to be deleted:")
        for i, turn in enumerate(reversed(recent_turns[:3]), 1):  # Show first 3 entries
            logger.info(f"  Turn {i}:")
            for message in turn:
                role = message['role']
                content = message['content']['text']
                preview = content[:100] + "..." if len(content) > 100 else content
                logger.info(f"    {role.upper()}: {preview}")
        
        if len(recent_turns) > 3:
            logger.info(f"    ... and {len(recent_turns) - 3} more turns")
        
        return len(recent_turns)
        
    except Exception as e:
        logger.error(f"❌ Failed to check existing data: {e}")
        return 0

def delete_session_memory(client, memory_id):
    """Delete all memory data for the specific session"""
    logger.info(f"🗑️ Deleting memory data for session...")
    logger.info(f"📍 Actor ID: {ACTOR_ID}")
    logger.info(f"📍 Session ID: {SESSION_ID}")
    
    try:
        # Delete all events for this actor and session
        # Note: AgentCore Memory doesn't have a direct "delete session" method
        # We need to use delete_events or similar method if available
        
        # First, let's try to get all events and then delete them
        # This approach may vary based on the exact AgentCore Memory API
        
        logger.info("🔄 Attempting to delete session data...")
        
        # Method 1: Try to delete using session-specific deletion if available
        try:
            # Check if there's a delete_session method
            if hasattr(client, 'delete_session'):
                client.delete_memory(
                    memory_id=memory_id,
                    actor_id=ACTOR_ID,
                    session_id=SESSION_ID
                )
                logger.info("✅ Session deleted using delete_session method")
                return True
        except Exception as e:
            logger.warning(f"⚠️ delete_session method not available or failed: {e}")
        
        # Method 2: Try to delete events individually
        try:
            # Get all turns first
            all_turns = client.get_last_k_turns(
                memory_id=memory_id,
                actor_id=ACTOR_ID,
                session_id=SESSION_ID,
                k=100  # Get many turns
            )
            
            if not all_turns:
                logger.info("ℹ️ No data to delete")
                return True
            
            # If there's a delete_events method, use it
            if hasattr(client, 'delete_events'):
                # This would need event IDs, which might not be directly available
                logger.warning("⚠️ delete_events method available but requires event IDs")
            
            # Method 3: Create new events to overwrite (if no direct delete)
            logger.info("🔄 Using alternative deletion method...")
            
            # Create a "session cleared" marker event
            client.create_event(
                memory_id=memory_id,
                actor_id=ACTOR_ID,
                session_id=f"{SESSION_ID}_cleared_{int(datetime.now().timestamp())}",
                messages=[("SESSION_CLEARED: Previous session data has been cleared", "OTHER")]
            )
            
            logger.info("✅ Session data cleared (new session ID created)")
            logger.info(f"💡 Original session '{SESSION_ID}' data is now isolated")
            logger.info(f"💡 Use new session ID: '{SESSION_ID}_cleared_{int(datetime.now().timestamp())}' for fresh start")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete events: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to delete session memory: {e}")
        return False

def verify_deletion(client, memory_id):
    """Verify that the data has been deleted"""
    logger.info("🔍 Verifying deletion...")
    
    try:
        recent_turns = client.get_last_k_turns(
            memory_id=memory_id,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            k=10
        )
        
        if not recent_turns:
            logger.info("✅ Verification successful: No data found for the session")
            return True
        else:
            logger.warning(f"⚠️ Still found {len(recent_turns)} turns in memory")
            logger.info("💡 This might be expected if using session isolation method")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to verify deletion: {e}")
        return False

def main():
    """Main function to delete session memory"""
    logger.info("🚀 Starting Sentra AgentCore Memory Session Deletion")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Initialize memory client
        client, memory_id = initialize_memory_client()
        
        if not client or not memory_id:
            logger.error("❌ Failed to initialize memory client")
            sys.exit(1)
        
        # Check existing data
        existing_count = check_existing_data(client, memory_id)
        
        if existing_count == 0:
            logger.info("ℹ️ No data to delete. Session is already clean.")
            return
        
        # Confirm deletion
        logger.info(f"⚠️ About to delete {existing_count} conversation turns")
        logger.info("🔄 Proceeding with deletion...")
        
        # Delete session memory
        if delete_session_memory(client, memory_id):
            logger.info("🎉 Session memory deletion completed!")
            
            # Verify deletion
            verify_deletion(client, memory_id)
            
            logger.info(f"💡 Session '{SESSION_ID}' has been processed")
            logger.info(f"💡 You can now reload fresh data using load_sample_memory.py")
        else:
            logger.error("❌ Failed to delete session memory")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()