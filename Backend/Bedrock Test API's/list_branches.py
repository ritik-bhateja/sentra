#!/usr/bin/env python3
"""
List Branches in a Session for Sentra AgentCore Memory

This script lists all branches in a specific session using the list_branches API.
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
ACTOR_ID = "harsh_kumar"  # The actor we want to list branches for
SESSION_ID = "1769672044577_uThicMyEirl0ZTigjkf"  # The session we want to list branches for

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

def list_branches(client, memory_id):
    """List branches in a session using the list_branches API"""
    logger.info(f"📋 Listing branches in session...")
    logger.info(f"📍 Memory ID: {memory_id}")
    logger.info(f"📍 Actor ID: {ACTOR_ID}")
    logger.info(f"📍 Session ID: {SESSION_ID}")
    
    try:
        # Call list_branches method
        response = client.list_branches(
            memory_id=memory_id,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID
        )
        
        logger.info("✅ Successfully retrieved branches using list_branches")
        logger.info(response);
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to list branches: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return None

def display_branches(response):
    """Display the branches information"""
    if not response:
        logger.info("ℹ️ No branch data to display")
        return
    
    logger.info("\n📋 BRANCHES RESPONSE:")
    logger.info("=" * 60)
    
    # Display the full response structure
    for key, value in response.items():
        if key == 'branches' and isinstance(value, list):
            logger.info(f"📊 Found {len(value)} branches")
            
            if value:
                logger.info("\n🌿 BRANCHES:")
                logger.info("-" * 40)
                
                for i, branch in enumerate(value, 1):
                    logger.info(f"\n🔸 Branch {i}:")
                    
                    # Display branch details
                    for branch_key, branch_value in branch.items():
                        if branch_key == 'branchId':
                            logger.info(f"   🆔 {branch_key}: {branch_value}")
                        elif branch_key == 'createdAt':
                            logger.info(f"   📅 {branch_key}: {branch_value}")
                        elif branch_key == 'lastModifiedAt':
                            logger.info(f"   🔄 {branch_key}: {branch_value}")
                        elif branch_key == 'messageCount':
                            logger.info(f"   💬 {branch_key}: {branch_value}")
                        elif branch_key == 'status':
                            logger.info(f"   📊 {branch_key}: {branch_value}")
                        else:
                            logger.info(f"   {branch_key}: {branch_value}")
            else:
                logger.info("ℹ️ No branches found in this session")
        else:
            logger.info(f"{key}: {value}")
    
    # Display pagination info if available
    if 'nextToken' in response and response['nextToken']:
        logger.info(f"\n📄 Next Token Available: {response['nextToken'][:50]}...")
        logger.info("💡 Use this token to get more branches")

def display_branch_summary(response):
    """Display a summary of branches"""
    if not response or 'branches' not in response:
        logger.info("ℹ️ No branch data for summary")
        return
    
    branches = response['branches']
    if not branches:
        logger.info("ℹ️ No branches found")
        return
    
    logger.info("\n📊 BRANCH SUMMARY:")
    logger.info("=" * 40)
    
    # Count branches by status if available
    status_counts = {}
    total_messages = 0
    
    for branch in branches:
        status = branch.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        total_messages += branch.get('messageCount', 0)
    
    logger.info(f"🔹 Total Branches: {len(branches)}")
    logger.info(f"🔹 Total Messages: {total_messages}")
    
    if status_counts:
        logger.info("🔹 Branch Status:")
        for status, count in status_counts.items():
            logger.info(f"   • {status}: {count}")
    
    # Show branch IDs
    logger.info("\n📝 Branch Details:")
    for i, branch in enumerate(branches, 1):
        branch_id = branch.get('branchId', 'Unknown')
        message_count = branch.get('messageCount', 0)
        status = branch.get('status', 'unknown')
        logger.info(f"   {i}. {branch_id}")
        logger.info(f"      Messages: {message_count}")
        logger.info(f"      Status: {status}")
        logger.info("")

def main():
    """Main function to list branches"""
    logger.info("🚀 Starting Sentra AgentCore Branches Listing")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Initialize memory client
        client, memory_id = initialize_memory_client()
        
        if not client or not memory_id:
            logger.error("❌ Failed to initialize memory client")
            sys.exit(1)
        
        # List branches
        response = list_branches(client, memory_id)
        
        if response:
            logger.info("🎉 Branches listing completed successfully!")
            
            # Display the response
            display_branches(response)
            
            # Show summary
            display_branch_summary(response)
            
            # Show next steps
            logger.info("\n💡 NEXT STEPS:")
            logger.info("   • Use view_store_memory.py to inspect specific sessions")
            logger.info("   • Use delete_specific_event.py to delete specific events")
            logger.info("   • Use clear_memory_session.py to create fresh sessions")
            
        else:
            logger.error("❌ Failed to retrieve branches")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()