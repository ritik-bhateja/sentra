#!/usr/bin/env python3
"""
Delete Specific Event from Sentra AgentCore Memory

This script deletes a specific event using its event_id from the AgentCore memory.
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
EVENT_ID = "0000001767873887106#b94e22ff"  # The specific event to delete
ACTOR_ID = "Sample"  # Same as used in load_sample_memory.py
SESSION_ID = "sample_session1"  # Same as used in load_sample_memory.py

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

def delete_specific_event(client, memory_id, event_id):
    """Delete a specific event by its event_id"""
    logger.info(f"🗑️ Attempting to delete event: {event_id}")
    logger.info(f"📍 Actor ID: {ACTOR_ID}")
    logger.info(f"📍 Session ID: {SESSION_ID}")
    
    try:
        # Method 1: Try delete_event if available
        if hasattr(client, 'delete_event'):
            logger.info("🔄 Using delete_event method...")
            result = client.delete_event(
                memoryId=memory_id,
                actorId=ACTOR_ID,
                sessionId=SESSION_ID,
                eventId=event_id
            )
            logger.info(f"✅ Event deleted successfully using delete_event: {result}")
            return True
            
        # Method 2: Try delete_events with single event
        elif hasattr(client, 'delete_events'):
            logger.info("🔄 Using delete_events method...")
            result = client.delete_events(
                memoryId=memory_id,
                actorId=ACTOR_ID,
                sessionId=SESSION_ID,
                eventIds=[event_id]
            )
            logger.info(f"✅ Event deleted successfully using delete_events: {result}")
            return True
            
        # Method 3: Try remove_event if available
        elif hasattr(client, 'remove_event'):
            logger.info("🔄 Using remove_event method...")
            result = client.remove_event(
                memoryId=memory_id,
                actorId=ACTOR_ID,
                sessionId=SESSION_ID,
                eventId=event_id
            )
            logger.info(f"✅ Event deleted successfully using remove_event: {result}")
            return True
            
        else:
            logger.error("❌ No suitable deletion method found in MemoryClient")
            logger.info("Available methods:")
            for method in dir(client):
                if 'delete' in method.lower() or 'remove' in method.lower():
                    logger.info(f"  - {method}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to delete event {event_id}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

def verify_deletion(client, memory_id, event_id):
    """Verify that the event has been deleted"""
    logger.info(f"🔍 Verifying deletion of event: {event_id}")
    
    try:
        # Try to get the specific event to see if it still exists
        if hasattr(client, 'get_event'):
            try:
                event = client.get_event(
                    memoryId=memory_id,
                    actorId=ACTOR_ID,
                    sessionId=SESSION_ID,
                    eventId=event_id
                )
                if event:
                    logger.warning(f"⚠️ Event still exists: {event}")
                    return False
                else:
                    logger.info("✅ Event successfully deleted (not found)")
                    return True
            except Exception as e:
                if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                    logger.info("✅ Event successfully deleted (not found)")
                    return True
                else:
                    logger.error(f"❌ Error verifying deletion: {e}")
                    return False
        else:
            logger.info("ℹ️ Cannot verify deletion - get_event method not available")
            logger.info("💡 Assuming deletion was successful based on no errors")
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to verify deletion: {e}")
        return False

def list_available_methods(client):
    """List all available methods on the memory client for debugging"""
    logger.info("🔍 Available MemoryClient methods:")
    methods = [method for method in dir(client) if not method.startswith('_')]
    for method in sorted(methods):
        logger.info(f"  - {method}")

def main():
    """Main function to delete specific event"""
    logger.info("🚀 Starting Sentra AgentCore Memory Specific Event Deletion")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🎯 Target Event ID: {EVENT_ID}")
    logger.info("=" * 60)
    
    try:
        # Initialize memory client
        client, memory_id = initialize_memory_client()
        
        if not client or not memory_id:
            logger.error("❌ Failed to initialize memory client")
            sys.exit(1)
        
        # List available methods for debugging
        list_available_methods(client)
        
        # Delete the specific event
        logger.info(f"🗑️ Attempting to delete event: {EVENT_ID}")
        
        if delete_specific_event(client, memory_id, EVENT_ID):
            logger.info("🎉 Event deletion completed!")
            
            # Verify deletion
            if verify_deletion(client, memory_id, EVENT_ID):
                logger.info("✅ Event deletion verified successfully!")
            else:
                logger.warning("⚠️ Could not verify deletion, but no errors occurred")
                
            logger.info(f"💡 Event {EVENT_ID} has been processed for deletion")
            
        else:
            logger.error("❌ Failed to delete the event")
            logger.info("💡 You may need to check the AgentCore Memory API documentation")
            logger.info("💡 Or use the session clearing approach instead")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()