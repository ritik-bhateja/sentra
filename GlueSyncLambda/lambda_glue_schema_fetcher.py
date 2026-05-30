"""
AWS Lambda: Glue Schema Fetcher & Memory Loader
Fetches insurance_db schema from Glue and loads into AgentCore Memory

Flow:
1. Fetch schema from Glue
2. Check existing events in memory
3. Delete all events
4. Verify 0 events
5. Load new schema
6. Verify 1 event
"""

import json
import logging
import boto3
from bedrock_agentcore.memory import MemoryClient

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue = boto3.client('glue', region_name='ap-south-1')
MEMORY_NAME = "Sentra_Agent_Memory_V1"
ACTOR_ID = "schema_loader"
SESSION_ID = "insurance_schema_session"

def lambda_handler(event, context):
    """Fetch schema and load to memory"""
    logger.info("🚀 Lambda execution started")
    
    client = None
    memory_id = None
    backup_events = []
    
    try:
        # Step 1: Fetch schema FIRST (before touching memory)
        logger.info("\n📍 STEP 1: Fetch schema from Glue")
        schema = get_schema('insurance_db', 'insurance_data')
        schema_text = format_schema_text(schema)
        logger.info(f"✅ Fetched {schema['count']} columns")
        
        # Print all columns
        logger.info("\n📋 INSURANCE_DATA Columns:")
        logger.info("=" * 80)
        for i, col in enumerate(schema['columns'], 1):
            logger.info(f"{i:3d}. {col['name']:<40} {col['type'].upper()}")
        logger.info("=" * 80)
        
        # Validate schema has data
        if schema['count'] == 0:
            raise Exception("Schema fetch returned 0 columns - invalid schema")
        
        # Step 2: Initialize memory
        logger.info("\n📍 STEP 2: Initialize memory client")
        client, memory_id = init_memory()
        logger.info(f"✅ Memory ID: {memory_id}")
        
        # Step 3: Check existing events and BACKUP
        logger.info("\n📍 STEP 3: Check existing events")
        backup_events = list_events(client, memory_id)
        logger.info(f"📊 Found {len(backup_events)} existing events")
        
        if backup_events:
            logger.info(f"💾 Backing up {len(backup_events)} events before deletion")
        
        # Step 4: Delete all events
        if backup_events:
            logger.info("\n📍 STEP 4: Delete all events")
            delete_all(client, memory_id, backup_events)
            logger.info(f"✅ Deleted {len(backup_events)} events")
        else:
            logger.info("\n📍 STEP 4: No events to delete")
        
        # Step 5: Verify 0 events
        logger.info("\n📍 STEP 5: Verify 0 events")
        if not verify_count(client, memory_id, 0):
            logger.error("❌ Failed to verify 0 events after deletion")
            # Restore backup
            restore_backup(client, memory_id, backup_events)
            raise Exception("Event count != 0 after deletion")
        
        # Step 6: Load schema
        logger.info("\n📍 STEP 6: Load schema to memory")
        load_schema(client, memory_id, schema_text)
        logger.info("✅ Schema loaded")
        
        # Step 7: Verify 1 event
        logger.info("\n📍 STEP 7: Verify 1 event")
        if not verify_count(client, memory_id, 1):
            events = list_events(client, memory_id)
            logger.error(f"⚠️ WARNING: Found {len(events)} events instead of 1!")
            for i, e in enumerate(events, 1):
                logger.error(f"   {i}. {e.get('eventId')} - {e.get('eventTimestamp')}")
            
            # Restore backup if verification fails
            logger.warning("🔄 Restoring backup events due to verification failure")
            restore_backup(client, memory_id, backup_events)
            raise Exception(f"Event count is {len(events)}, expected 1")
        
        logger.info("\n🎉 SUCCESS! Schema loaded to memory")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'memory_id': memory_id,
                'actor_id': ACTOR_ID,
                'session_id': SESSION_ID,
                'columns': schema['count'],
                'event_count': 1,
                'backup_events_count': len(backup_events)
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        
        # Attempt to restore backup if we have it
        if client and memory_id and backup_events:
            logger.warning("🔄 Attempting to restore backup events due to error")
            try:
                restore_backup(client, memory_id, backup_events)
                logger.info(f"✅ Restored {len(backup_events)} backup events")
            except Exception as restore_error:
                logger.error(f"❌ Failed to restore backup: {restore_error}", exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'backup_restored': bool(backup_events)
            })
        }

def get_schema(db_name, table_name):
    """Get table schema from Glue with error handling"""
    try:
        response = glue.get_table(DatabaseName=db_name, Name=table_name)
        columns = response['Table']['StorageDescriptor']['Columns']
        
        if not columns:
            raise Exception(f"No columns found in {db_name}.{table_name}")
        
        return {
            'database': db_name,
            'table': table_name,
            'columns': [{'name': c['Name'], 'type': c['Type']} for c in columns],
            'count': len(columns)
        }
    except Exception as e:
        logger.error(f"Failed to fetch schema from Glue: {e}")
        raise Exception(f"Glue schema fetch failed: {str(e)}")

def format_schema_text(schema):
    """Format schema as text for memory"""
    text = f"INSURANCE_DATA Table Columns\n{'='*80}\n"
    for col in schema['columns']:
        text += f"- {col['name']} ({col['type'].upper()})\n"
    text += f"\nTotal: {schema['count']} columns"
    return text

def init_memory():
    """Initialize memory client"""
    client = MemoryClient(region_name='ap-south-1')
    memories = client.list_memories()
    existing = next((m for m in memories if m["id"].startswith(MEMORY_NAME)), None)
    
    if existing:
        return client, existing["id"]
    
    logger.info(f"🆕 Creating new memory: {MEMORY_NAME}")
    memory = client.create_memory_and_wait(
        name=MEMORY_NAME,
        strategies=[],
        description="Sentra agent memory",
        event_expiry_days=7
    )
    return client, memory["id"]

def list_events(client, memory_id):
    """List all events in session"""
    try:
        events = client.list_events(
            memory_id=memory_id,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID
        )
        return events if events else []
    except Exception as e:
        logger.warning(f"Failed to list events: {e}")
        return []

def delete_all(client, memory_id, events):
    """Delete all events"""
    for i, event in enumerate(events, 1):
        event_id = event.get('eventId')
        logger.info(f"   Deleting event {i}/{len(events)}: {event_id}")
        try:
            if hasattr(client, 'delete_event'):
                client.delete_event(
                    memoryId=memory_id,
                    actorId=ACTOR_ID,
                    sessionId=SESSION_ID,
                    eventId=event_id
                )
            elif hasattr(client, 'delete_events'):
                client.delete_events(
                    memoryId=memory_id,
                    actorId=ACTOR_ID,
                    sessionId=SESSION_ID,
                    eventIds=[event_id]
                )
        except Exception as e:
            logger.error(f"⚠️ Failed to delete {event_id}: {e}")

def verify_count(client, memory_id, expected):
    """Verify event count"""
    events = list_events(client, memory_id)
    actual = len(events)
    logger.info(f"🔍 Expected: {expected}, Actual: {actual}")
    
    if actual != expected:
        logger.error(f"❌ Verification failed: Expected {expected} but found {actual}")
        return False
    
    logger.info(f"✅ Verification passed: {actual} events")
    return True

def load_schema(client, memory_id, schema_text):
    """Load schema to memory"""
    try:
        client.create_event(
            memory_id=memory_id,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            messages=[(schema_text, "OTHER")]
        )
    except Exception as e:
        logger.error(f"Failed to load schema to memory: {e}")
        raise Exception(f"Memory load failed: {str(e)}")

def restore_backup(client, memory_id, backup_events):
    """Restore backup events to memory"""
    if not backup_events:
        logger.info("No backup events to restore")
        return
    
    logger.info(f"🔄 Restoring {len(backup_events)} backup events...")
    
    restored_count = 0
    for i, event in enumerate(backup_events, 1):
        try:
            # Extract content from event payload
            if 'payload' in event and isinstance(event['payload'], list):
                for payload_item in event['payload']:
                    if isinstance(payload_item, dict) and 'conversational' in payload_item:
                        conv = payload_item['conversational']
                        role = conv.get('role', 'OTHER')
                        content = conv.get('content', {}).get('text', '')
                        
                        if content:
                            # Recreate event
                            client.create_event(
                                memory_id=memory_id,
                                actor_id=ACTOR_ID,
                                session_id=SESSION_ID,
                                messages=[(content, role)]
                            )
                            restored_count += 1
                            logger.info(f"   Restored event {i}/{len(backup_events)}")
        except Exception as e:
            logger.error(f"Failed to restore event {i}: {e}")
    
    logger.info(f"✅ Restored {restored_count}/{len(backup_events)} events")
    
    # Verify restoration
    current_events = list_events(client, memory_id)
    logger.info(f"📊 Current event count after restoration: {len(current_events)}")

if __name__ == "__main__":
    # Local test
    result = lambda_handler({}, None)
    print(f"\n{json.dumps(json.loads(result['body']), indent=2)}")
