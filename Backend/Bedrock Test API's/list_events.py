#!/usr/bin/env python3
"""
List Events for Sentra AgentCore Memory

This script lists events using the list_events API.
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
ACTOR_ID = "harsh_kumar"  # The actor we want to list events for
SESSION_ID = "1768302286603_Jrma8WvGSECDdSuwmsB"  # The session we want tzo list events for

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

def list_events(client, memory_id):
    """List events using the list_events API"""
    logger.info(f"📋 Listing events...")
    logger.info(f"📍 Memory ID: {memory_id}")
    logger.info(f"📍 Actor ID: {ACTOR_ID}")
    logger.info(f"📍 Session ID: {SESSION_ID}")
    
    try:
        # Call list_events method
        response = client.list_events(
            memory_id=memory_id,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID
        )
        
        logger.info("✅ Successfully retrieved events using list_events")
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to list events: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return None

def display_events(response):
    """Display the events information"""
    if not response:
        logger.info("ℹ️ No event data to display")
        return
    
    logger.info("\n📋 EVENTS RESPONSE:")
    logger.info("=" * 60)
    
    # The response is directly a list of events
    if isinstance(response, list):
        events = response
        logger.info(f"� Found {len(events)} events")
        
        if events:
            logger.info("\n🎯 EVENTS:")
            logger.info("-" * 40)
            
            for i, event in enumerate(events, 1):
                logger.info(f"\n🔸 Event {i}:")
                
                # Display event details
                for event_key, event_value in event.items():
                    if event_key == 'eventId':
                        logger.info(f"   🆔 {event_key}: {event_value}")
                    elif event_key == 'eventTimestamp':
                        logger.info(f"   📅 {event_key}: {event_value}")
                    elif event_key == 'memoryId':
                        logger.info(f"   🧠 {event_key}: {event_value}")
                    elif event_key == 'actorId':
                        logger.info(f"   👤 {event_key}: {event_value}")
                    elif event_key == 'sessionId':
                        logger.info(f"   📝 {event_key}: {event_value}")
                    elif event_key == 'payload':
                        logger.info(f"   � {event_key}:")
                        # Handle payload which is a list
                        if isinstance(event_value, list):
                            for j, payload_item in enumerate(event_value):
                                logger.info(f"      Payload {j+1}:")
                                if isinstance(payload_item, dict) and 'conversational' in payload_item:
                                    conv = payload_item['conversational']
                                    if 'role' in conv:
                                        logger.info(f"         Role: {conv['role']}")
                                    if 'content' in conv and 'text' in conv['content']:
                                        content = conv['content']['text']
                                        # Show first line and truncate
                                        first_line = content.split('\n')[0]
                                        logger.info(f"         Content: {first_line}")
                                        if len(content) > 200:
                                            logger.info(f"         ... (truncated, {len(content)} total chars)")
                    elif event_key == 'branch':
                        logger.info(f"   🌿 {event_key}: {event_value}")
                    else:
                        logger.info(f"   {event_key}: {event_value}")
        else:
            logger.info("ℹ️ No events found")
    else:
        # Handle dictionary response format
        logger.info(f"📄 Response type: {type(response)}")
        if isinstance(response, dict):
            for key, value in response.items():
                logger.info(f"{key}: {value}")
        else:
            logger.info(f"Raw response: {response}")

def display_event_summary(response):
    """Display a summary of events"""
    if not response:
        logger.info("ℹ️ No event data for summary")
        return
    
    # Handle list response format
    events = response if isinstance(response, list) else response.get('events', [])
    
    if not events:
        logger.info("ℹ️ No events found")
        return
    
    logger.info("\n📊 EVENT SUMMARY:")
    logger.info("=" * 40)
    
    # Count events by role and branch
    role_counts = {}
    branch_counts = {}
    content_types = {}
    
    for event in events:
        # Extract role from payload
        if 'payload' in event and isinstance(event['payload'], list):
            for payload_item in event['payload']:
                if isinstance(payload_item, dict) and 'conversational' in payload_item:
                    role = payload_item['conversational'].get('role', 'unknown')
                    role_counts[role] = role_counts.get(role, 0) + 1
                    
                    # Check content type
                    content = payload_item['conversational'].get('content', {}).get('text', '')
                    if content.startswith('SCHEMA_DATA_'):
                        content_type = content.split(':')[0].replace('SCHEMA_DATA_', '')
                        content_types[content_type] = content_types.get(content_type, 0) + 1
                    elif content.startswith('INSURANCE_DATA'):
                        content_types['TABLE_COLUMNS'] = content_types.get('TABLE_COLUMNS', 0) + 1
        
        # Extract branch info
        if 'branch' in event:
            branch_name = event['branch'].get('name', 'unknown')
            branch_counts[branch_name] = branch_counts.get(branch_name, 0) + 1
    
    logger.info(f"🔹 Total Events: {len(events)}")
    
    if role_counts:
        logger.info("🔹 Event Roles:")
        for role, count in role_counts.items():
            logger.info(f"   • {role}: {count}")
    
    if content_types:
        logger.info("🔹 Content Types:")
        for content_type, count in content_types.items():
            logger.info(f"   • {content_type}: {count}")
    
    if branch_counts:
        logger.info("🔹 Branch Distribution:")
        for branch_name, count in branch_counts.items():
            logger.info(f"   • {branch_name}: {count}")
    
    # Show recent events
    logger.info("\n📝 Event Details (First 20):")
    for i, event in enumerate(events[:20], 1):
        event_id = event.get('eventId', 'Unknown')
        timestamp = event.get('eventTimestamp', 'unknown')
        
        logger.info(f"   {i}. Event ID: {event_id}")
        logger.info(f"      Timestamp: {timestamp}")
        
        # Show content preview
        if 'payload' in event and isinstance(event['payload'], list):
            for payload_item in event['payload']:
                if isinstance(payload_item, dict) and 'conversational' in payload_item:
                    role = payload_item['conversational'].get('role', 'unknown')
                    content = payload_item['conversational'].get('content', {}).get('text', '')
                    
                    logger.info(f"      Role: {role}")
                    
                    # Show content type or first line
                    if content.startswith('SCHEMA_DATA_'):
                        content_type = content.split(':')[0]
                        logger.info(f"      Type: {content_type}")
                    elif content.startswith('INSURANCE_DATA'):
                        logger.info(f"      Type: TABLE_COLUMNS")
                    else:
                        first_line = content.split('\n')[0][:100]
                        logger.info(f"      Content: {first_line}...")
        logger.info("")

def main():
    """Main function to list events"""
    logger.info("🚀 Starting Sentra AgentCore Events Listing")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Initialize memory client
        client, memory_id = initialize_memory_client()
        
        if not client or not memory_id:
            logger.error("❌ Failed to initialize memory client")
            sys.exit(1)
        
        # List events
        response = list_events(client, memory_id)
        
        if response:
            logger.info("🎉 Events listing completed successfully!")
            
            # Display the response
            display_events(response)
            
            # Show summary
            display_event_summary(response)
            
            # Show next steps
            logger.info("\n💡 NEXT STEPS:")
            logger.info("   • Use delete_specific_event.py to delete specific events")
            logger.info("   • Use view_store_memory.py to inspect specific sessions")
            logger.info("   • Use list_branches.py to see branch structure")
            
        else:
            logger.error("❌ Failed to retrieve events")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()