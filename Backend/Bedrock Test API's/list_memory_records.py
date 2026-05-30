#!/usr/bin/env python3
"""
List Memory Records for Sentra AgentCore Memory

This script lists memory records using the list_memory_records API.
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
NAMESPACE = "/summaries/harsh_kumar/1765956980033_3KPglwKjtK3G5IFcKWv"

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

def list_memory_records(client, memory_id):
    """List memory records using the list_memory_records API"""
    logger.info(f"📋 Listing memory records...")
    logger.info(f"📍 Memory ID: {memory_id}")
    logger.info(f"📍 Namespace: {NAMESPACE}")
    
    try:
        # Call list_memory_records with minimal required parameters
        response = client.list_memory_records(
            memoryId=memory_id,
            namespace=NAMESPACE
        )
        
        logger.info("✅ Successfully retrieved memory records")
        
        # Display the response
        if 'memoryRecords' in response:
            records = response['memoryRecords']
            logger.info(f"📊 Found {len(records)} memory records")
            
            if records:
                logger.info("📋 Memory Records:")
                logger.info("=" * 60)
                
                for i, record in enumerate(records, 1):
                    logger.info(f"\n🔸 Record {i}:")
                    
                    # Display record details
                    for key, value in record.items():
                        if key == 'content':
                            # Truncate long content
                            content_preview = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                            logger.info(f"   {key}: {content_preview}")
                        else:
                            logger.info(f"   {key}: {value}")
            else:
                logger.info("ℹ️ No memory records found")
        else:
            logger.info("ℹ️ No 'memoryRecords' key in response")
            logger.info(f"📄 Full response: {response}")
        
        # Display pagination info if available
        if 'nextToken' in response and response['nextToken']:
            logger.info(f"\n📄 Next Token Available: {response['nextToken'][:50]}...")
            logger.info("💡 Use this token to get more records")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to list memory records: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return None

def main():
    """Main function to list memory records"""
    logger.info("🚀 Starting Sentra AgentCore Memory Records Listing")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Initialize memory client
        client, memory_id = initialize_memory_client()
        
        if not client or not memory_id:
            logger.error("❌ Failed to initialize memory client")
            sys.exit(1)
        
        # List memory records
        response = list_memory_records(client, memory_id)
        
        if response:
            logger.info("🎉 Memory records listing completed successfully!")
            
            # Show summary
            record_count = len(response.get('memoryRecords', []))
            logger.info(f"📊 Total Records Found: {record_count}")
            
            if 'nextToken' in response:
                logger.info("📄 More records available (pagination)")
            
        else:
            logger.error("❌ Failed to retrieve memory records")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()