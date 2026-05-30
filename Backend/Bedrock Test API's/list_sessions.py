#!/usr/bin/env python3
"""
List Sessions for Sentra AgentCore Memory

This script lists sessions using the list_sessions API.
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
ACTOR_ID = "harsh_kumar"  # The actor we want to list sessions for

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

def list_sessions(client, memory_id):
    """List sessions using the list_sessions API"""
    logger.info(f"📋 Listing sessions...")
    logger.info(f"📍 Memory ID: {memory_id}")
    logger.info(f"📍 Actor ID: {ACTOR_ID}")
    
    try:
        # Call list_sessions with correct parameter names
        response = client.list_sessions(
            memoryId=memory_id,
            actorId=ACTOR_ID
        )
        
        logger.info("✅ Successfully retrieved sessions using list_sessions")
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to list sessions: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return None

def display_session_summary(response):
    """Display a summary of sessions"""
    if not response or 'sessions' not in response:
        logger.info("ℹ️ No session data to display")
        return
    
    sessions = response['sessions']
    if not sessions:
        logger.info("ℹ️ No sessions found")
        return
    
    logger.info("\n📊 SESSION SUMMARY:")
    logger.info("=" * 40)
    
    # Count sessions by pattern
    sample_sessions = [s for s in sessions if 'sample' in s.get('sessionId', '').lower()]
    other_sessions = [s for s in sessions if 'sample' not in s.get('sessionId', '').lower()]
    
    logger.info(f"🔹 Sample Sessions: {len(sample_sessions)}")
    logger.info(f"🔹 Other Sessions: {len(other_sessions)}")
    logger.info(f"🔹 Total Sessions: {len(sessions)}")
    
    # Show session IDs
    logger.info("\n📝 Session Details:")
    for i, session in enumerate(sessions, 1):
        session_id = session.get('sessionId', 'Unknown')
        message_count = session.get('messageCount', 0)
        status = session.get('status', 'unknown')
        logger.info(f"   {i}. {session_id}")
        logger.info(f"      Messages: {message_count}")
        logger.info(f"      Status: {status}")
        
        # Show other available fields
        for key, value in session.items():
            if key not in ['sessionId', 'messageCount', 'status']:
                logger.info(f"      {key}: {value}")
        logger.info("")

def main():
    """Main function to list sessions"""
    logger.info("🚀 Starting Sentra AgentCore Sessions Listing")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Initialize memory client
        client, memory_id = initialize_memory_client()
        
        if not client or not memory_id:
            logger.error("❌ Failed to initialize memory client")
            sys.exit(1)
        
        # List sessions
        response = list_sessions(client, memory_id)
        
        if response:
            logger.info("🎉 Sessions listing completed successfully!")
            
            # Display the response
            if 'sessions' in response:
                sessions = response['sessions']
                logger.info(f"📊 Found {len(sessions)} sessions")
                
                if sessions:
                    logger.info("📋 Sessions:")
                    logger.info("=" * 60)
                    
                    for i, session in enumerate(sessions, 1):
                        logger.info(f"\n🔸 Session {i}:")
                        
                        # Display session details
                        for key, value in session.items():
                            if key == 'sessionId':
                                logger.info(f"   🆔 {key}: {value}")
                            elif key == 'createdAt':
                                logger.info(f"   📅 {key}: {value}")
                            elif key == 'lastModifiedAt':
                                logger.info(f"   🔄 {key}: {value}")
                            elif key == 'messageCount':
                                logger.info(f"   💬 {key}: {value}")
                            else:
                                logger.info(f"   {key}: {value}")
                else:
                    logger.info("ℹ️ No sessions found for this actor")
            else:
                logger.info("ℹ️ No 'sessions' key in response")
                logger.info(f"📄 Full response: {response}")
            
            # Show summary
            display_session_summary(response)
            
            # Show next steps
            logger.info("\n💡 NEXT STEPS:")
            logger.info("   • Use view_store_memory.py to inspect specific sessions")
            logger.info("   • Use delete_specific_event.py to delete specific events")
            logger.info("   • Use clear_memory_session.py to create fresh sessions")
            
        else:
            logger.error("❌ Failed to retrieve sessions")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()