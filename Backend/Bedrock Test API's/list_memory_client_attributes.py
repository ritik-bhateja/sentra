#!/usr/bin/env python3
"""
List MemoryClient Attributes and Methods

This script lists all available attributes and methods on the MemoryClient object.
"""

import os
import sys
import logging
from bedrock_agentcore.memory import MemoryClient
from datetime import datetime
import inspect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
REGION = os.getenv("AWS_REGION", "ap-south-1")

def initialize_memory_client():
    """Initialize the memory client"""
    try:
        client = MemoryClient(region_name=REGION)
        logger.info(f"✅ Memory client initialized for region: {REGION}")
        return client
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize memory client: {e}")
        raise

def list_all_attributes(client):
    """List all attributes and methods of the MemoryClient"""
    logger.info("🔍 Analyzing MemoryClient attributes and methods...")
    
    # Get all attributes
    all_attributes = dir(client)
    
    # Categorize attributes
    public_methods = []
    private_methods = []
    properties = []
    special_methods = []
    
    for attr_name in all_attributes:
        try:
            attr = getattr(client, attr_name)
            
            if attr_name.startswith('__') and attr_name.endswith('__'):
                special_methods.append(attr_name)
            elif attr_name.startswith('_'):
                private_methods.append(attr_name)
            elif callable(attr):
                public_methods.append(attr_name)
            else:
                properties.append(attr_name)
                
        except Exception as e:
            logger.warning(f"Could not access attribute {attr_name}: {e}")
    
    # Display results
    logger.info("=" * 80)
    logger.info("📋 MEMORY CLIENT ANALYSIS")
    logger.info("=" * 80)
    
    # Public Methods
    logger.info(f"\n🔧 PUBLIC METHODS ({len(public_methods)}):")
    logger.info("-" * 50)
    for method in sorted(public_methods):
        try:
            method_obj = getattr(client, method)
            if hasattr(method_obj, '__doc__') and method_obj.__doc__:
                doc = method_obj.__doc__.strip().split('\n')[0][:100]
                logger.info(f"   • {method}() - {doc}")
            else:
                logger.info(f"   • {method}()")
        except:
            logger.info(f"   • {method}()")
    
    # Properties
    if properties:
        logger.info(f"\n📊 PROPERTIES ({len(properties)}):")
        logger.info("-" * 50)
        for prop in sorted(properties):
            try:
                value = getattr(client, prop)
                value_type = type(value).__name__
                logger.info(f"   • {prop}: {value_type}")
            except:
                logger.info(f"   • {prop}: (unable to access)")
    
    # Memory-related methods
    memory_methods = [m for m in public_methods if 'memory' in m.lower()]
    if memory_methods:
        logger.info(f"\n🧠 MEMORY-RELATED METHODS ({len(memory_methods)}):")
        logger.info("-" * 50)
        for method in sorted(memory_methods):
            logger.info(f"   • {method}()")
    
    # Session-related methods
    session_methods = [m for m in public_methods if 'session' in m.lower()]
    if session_methods:
        logger.info(f"\n📝 SESSION-RELATED METHODS ({len(session_methods)}):")
        logger.info("-" * 50)
        for method in sorted(session_methods):
            logger.info(f"   • {method}()")
    
    # Event-related methods
    event_methods = [m for m in public_methods if 'event' in m.lower()]
    if event_methods:
        logger.info(f"\n🎯 EVENT-RELATED METHODS ({len(event_methods)}):")
        logger.info("-" * 50)
        for method in sorted(event_methods):
            logger.info(f"   • {method}()")
    
    # List/Get methods
    list_get_methods = [m for m in public_methods if m.startswith(('list_', 'get_'))]
    if list_get_methods:
        logger.info(f"\n📋 LIST/GET METHODS ({len(list_get_methods)}):")
        logger.info("-" * 50)
        for method in sorted(list_get_methods):
            logger.info(f"   • {method}()")
    
    # Create/Delete methods
    crud_methods = [m for m in public_methods if any(m.startswith(prefix) for prefix in ['create_', 'delete_', 'remove_', 'update_'])]
    if crud_methods:
        logger.info(f"\n⚙️ CRUD METHODS ({len(crud_methods)}):")
        logger.info("-" * 50)
        for method in sorted(crud_methods):
            logger.info(f"   • {method}()")
    
    # Private methods (for debugging)
    if private_methods:
        logger.info(f"\n🔒 PRIVATE METHODS ({len(private_methods)}) - First 10:")
        logger.info("-" * 50)
        for method in sorted(private_methods)[:10]:
            logger.info(f"   • {method}")
        if len(private_methods) > 10:
            logger.info(f"   ... and {len(private_methods) - 10} more")
    
    return {
        'public_methods': public_methods,
        'properties': properties,
        'memory_methods': memory_methods,
        'session_methods': session_methods,
        'event_methods': event_methods,
        'list_get_methods': list_get_methods,
        'crud_methods': crud_methods
    }

def inspect_specific_methods(client, methods_of_interest):
    """Inspect specific methods in detail"""
    logger.info("\n🔬 DETAILED METHOD INSPECTION:")
    logger.info("=" * 60)
    
    for method_name in methods_of_interest:
        if hasattr(client, method_name):
            try:
                method = getattr(client, method_name)
                logger.info(f"\n📋 {method_name}:")
                
                # Get method signature
                try:
                    sig = inspect.signature(method)
                    logger.info(f"   Signature: {method_name}{sig}")
                except:
                    logger.info(f"   Signature: {method_name}(...)")
                
                # Get docstring
                if hasattr(method, '__doc__') and method.__doc__:
                    doc_lines = method.__doc__.strip().split('\n')
                    logger.info(f"   Description: {doc_lines[0]}")
                    if len(doc_lines) > 1:
                        logger.info("   Full doc available")
                else:
                    logger.info("   Description: No documentation available")
                    
            except Exception as e:
                logger.info(f"\n📋 {method_name}: Error inspecting - {e}")

def main():
    """Main function to analyze MemoryClient"""
    logger.info("🚀 Starting MemoryClient Attribute Analysis")
    logger.info(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Initialize memory client
        client = initialize_memory_client()
        
        # List all attributes
        analysis = list_all_attributes(client)
        
        # Inspect key methods in detail
        key_methods = [
            'list_sessions', 'list_memories', 'list_memory_records',
            'create_event', 'delete_event', 'get_last_k_turns',
            'create_memory', 'delete_memory'
        ]
        
        available_key_methods = [m for m in key_methods if m in analysis['public_methods']]
        if available_key_methods:
            inspect_specific_methods(client, available_key_methods)
        
        # Summary
        logger.info("\n📊 SUMMARY:")
        logger.info("=" * 40)
        logger.info(f"Total Public Methods: {len(analysis['public_methods'])}")
        logger.info(f"Memory Methods: {len(analysis['memory_methods'])}")
        logger.info(f"Session Methods: {len(analysis['session_methods'])}")
        logger.info(f"Event Methods: {len(analysis['event_methods'])}")
        logger.info(f"List/Get Methods: {len(analysis['list_get_methods'])}")
        logger.info(f"CRUD Methods: {len(analysis['crud_methods'])}")
        
        logger.info("\n🎉 MemoryClient analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()