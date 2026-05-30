#!/usr/bin/env python3
"""
Get Specific Event from Sentra AgentCore Memory

This script retrieves a specific event by its event ID using the get_event API.
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
ACTOR_ID = "Sample"  # The actor ID
SESSION_ID = "sample_session1"  # The session ID
EVENT_ID = "0000001767876305148#8bb62a46"  # Default event ID (can be changed)

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

def get_event(client, memory_id, event_id):
    """Get a specific event using the get_event API"""
    logger.info(f"🔍 Getting specific event...")
    logger.info(f"📍 Memory ID: {memory_id}")
    logger.info(f"📍 Actor ID: {ACTOR_ID}")
    logger.info(f"📍 Session ID: {SESSION_ID}")
    logger.info(f"📍 Event ID: {event_id}")
    
    try:
        # Call get_event method
        response = client.get_event(
            memoryId=memory_id,
            actorId=ACTOR_ID,
            sessionId=SESSION_ID,
            eventId=event_id
        )
        
        logger.info("✅ Successfully retrieved event using get_event")
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to get event: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return None

def display_event_details(event):
    """Display detailed information about the event"""
    if not event:
        logger.info("ℹ️ No event data to display")
        return
    
    logger.info("\n📋 EVENT DETAILS:")
    logger.info("=" * 60)
    
    # Display basic event information
    for key, value in event.items():
        if key == 'eventId':
            logger.info(f"🆔 Event ID: {value}")
        elif key == 'eventTimestamp':
            logger.info(f"📅 Timestamp: {value}")
        elif key == 'memoryId':
            logger.info(f"🧠 Memory ID: {value}")
        elif key == 'actorId':
            logger.info(f"👤 Actor ID: {value}")
        elif key == 'sessionId':
            logger.info(f"📝 Session ID: {value}")
        elif key == 'payload':
            logger.info(f"📦 Payload:")
            display_payload_details(value)
        elif key == 'branch':
            logger.info(f"🌿 Branch: {value}")
        else:
            logger.info(f"{key}: {value}")

def display_payload_details(payload):
    """Display detailed payload information"""
    if not payload or not isinstance(payload, list):
        logger.info("   No payload data")
        return
    
    for i, payload_item in enumerate(payload, 1):
        logger.info(f"\n   📦 Payload Item {i}:")
        
        if isinstance(payload_item, dict) and 'conversational' in payload_item:
            conv = payload_item['conversational']
            
            # Display role
            if 'role' in conv:
                logger.info(f"      👤 Role: {conv['role']}")
            
            # Display content
            if 'content' in conv and 'text' in conv['content']:
                content = conv['content']['text']
                logger.info(f"      📝 Content:")
                
                # Check if it's schema data
                if content.startswith('SCHEMA_DATA_'):
                    content_type = content.split(':')[0]
                    logger.info(f"         Type: {content_type}")
                    
                    # Show first few lines
                    lines = content.split('\n')
                    logger.info(f"         Preview:")
                    for line in lines[:5]:
                        if line.strip():
                            logger.info(f"           {line.strip()}")
                    
                    if len(lines) > 5:
                        logger.info(f"           ... ({len(lines)-5} more lines)")
                        
                elif content.startswith('INSURANCE_DATA'):
                    logger.info(f"         Type: TABLE_COLUMNS")
                    logger.info(f"         Preview: INSURANCE_DATA Table with 142 columns")
                    
                    # Count columns
                    column_lines = [line for line in content.split('\n') if line.strip().startswith('- ')]
                    logger.info(f"         Column Count: {len(column_lines)}")
                    
                    # Show first few columns
                    logger.info(f"         First 5 Columns:")
                    for line in column_lines[:5]:
                        logger.info(f"           {line.strip()}")
                    
                    if len(column_lines) > 5:
                        logger.info(f"           ... ({len(column_lines)-5} more columns)")
                        
                else:
                    # Regular content
                    lines = content.split('\n')
                    logger.info(f"         Text ({len(content)} chars, {len(lines)} lines):")
                    
                    # Show first few lines
                    for line in lines[:3]:
                        if line.strip():
                            logger.info(f"           {line.strip()}")
                    
                    if len(lines) > 3:
                        logger.info(f"           ... ({len(lines)-3} more lines)")
        else:
            logger.info(f"      Raw payload: {payload_item}")

def display_event_summary(event):
    """Display a summary of the event"""
    if not event:
        return
    
    logger.info("\n📊 EVENT SUMMARY:")
    logger.info("=" * 40)
    
    # Basic info
    event_id = event.get('eventId', 'Unknown')
    timestamp = event.get('eventTimestamp', 'Unknown')
    
    logger.info(f"🔹 Event ID: {event_id}")
    logger.info(f"🔹 Created: {timestamp}")
    
    # Analyze payload
    if 'payload' in event and isinstance(event['payload'], list):
        payload_count = len(event['payload'])
        logger.info(f"🔹 Payload Items: {payload_count}")
        
        for payload_item in event['payload']:
            if isinstance(payload_item, dict) and 'conversational' in payload_item:
                conv = payload_item['conversational']
                role = conv.get('role', 'unknown')
                content = conv.get('content', {}).get('text', '')
                
                logger.info(f"🔹 Role: {role}")
                logger.info(f"🔹 Content Length: {len(content)} characters")
                
                # Identify content type
                if content.startswith('SCHEMA_DATA_'):
                    content_type = content.split(':')[0].replace('SCHEMA_DATA_', '')
                    logger.info(f"🔹 Content Type: {content_type}")
                elif content.startswith('INSURANCE_DATA'):
                    logger.info(f"🔹 Content Type: TABLE_COLUMNS")
                else:
                    logger.info(f"🔹 Content Type: TEXT")

def main():
    """Main function to get specific event"""
    logger.info("🚀 Starting Sentra AgentCore Get Event")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Allow event ID to be passed as command line argument
    event_id = sys.argv[1] if len(sys.argv) > 1 else EVENT_ID
    logger.info(f"🎯 Target Event ID: {event_id}")
    
    try:
        # Initialize memory client
        client, memory_id = initialize_memory_client()
        
        if not client or not memory_id:
            logger.error("❌ Failed to initialize memory client")
            sys.exit(1)
        
        # Get the specific event
        event = get_event(client, memory_id, event_id)
        
        if event:
            logger.info("🎉 Event retrieval completed successfully!")
            
            # Display the event details
            display_event_details(event)
            
            # Show summary
            display_event_summary(event)
            
            # Show next steps
            logger.info("\n💡 NEXT STEPS:")
            logger.info("   • Use delete_specific_event.py to delete this event")
            logger.info("   • Use list_events.py to see all events")
            logger.info("   • Use view_store_memory.py to inspect the session")
            
        else:
            logger.error("❌ Failed to retrieve event or event not found")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()