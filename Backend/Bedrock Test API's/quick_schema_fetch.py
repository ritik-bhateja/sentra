#!/usr/bin/env python3
"""
Quick Schema Fetcher for Sentra Project
Quickly fetch and display schema information for specific databases/tables
"""

import boto3
import json
from typing import List, Dict, Any

def fetch_table_columns(database_name: str, table_name: str) -> Dict[str, Any]:
    """
    Quickly fetch complete schema information for a specific table
    
    Args:
        database_name: Name of the database
        table_name: Name of the table
        
    Returns:
        Dictionary with complete table schema information
    """
    try:
        glue_client = boto3.client('glue', region_name='ap-south-1')
        
        response = glue_client.get_table(
            DatabaseName=database_name,
            Name=table_name
        )
        
        table = response['Table']
        storage_descriptor = table.get('StorageDescriptor', {})
        
        # Extract columns
        columns = []
        for col in storage_descriptor.get('Columns', []):
            columns.append({
                'name': col['Name'],
                'type': col['Type'],
                'comment': col.get('Comment', '')
            })
        
        # Extract partition keys
        partition_keys = []
        for pk in table.get('PartitionKeys', []):
            partition_keys.append({
                'name': pk['Name'],
                'type': pk['Type'],
                'comment': pk.get('Comment', '')
            })
        
        # Return complete schema information
        return {
            'columns': columns,
            'partition_keys': partition_keys,
            'table_type': table.get('TableType', ''),
            'location': storage_descriptor.get('Location', ''),
            'input_format': storage_descriptor.get('InputFormat', ''),
            'output_format': storage_descriptor.get('OutputFormat', ''),
            'serde_info': storage_descriptor.get('SerdeInfo', {}),
            'parameters': table.get('Parameters', {}),
            'create_time': str(table.get('CreateTime', '')),
            'update_time': str(table.get('UpdateTime', ''))
        }
        
    except Exception as e:
        print(f"❌ Error fetching {database_name}.{table_name}: {e}")
        return {}

def generate_prompt_schema(database_name: str, table_name: str) -> str:
    """
    Generate schema text suitable for prompt inclusion
    
    Args:
        database_name: Name of the database
        table_name: Name of the table
        
    Returns:
        Formatted schema text
    """
    schema_info = fetch_table_columns(database_name, table_name)
    
    if not schema_info or not schema_info.get('columns'):
        return f"# {table_name.upper()} - Schema unavailable"
    
    columns = schema_info['columns']
    partition_keys = schema_info.get('partition_keys', [])
    
    schema_text = f"\n{table_name.upper()} Table Columns\n"
    schema_text += "=" * 80 + "\n"
    
    # Add regular columns
    for col in columns:
        comment = f" -- {col['comment']}" if col['comment'] else ""
        schema_text += f"- {col['name']} ({col['type'].upper()}){comment}\n"
    
    # Add partition keys if they exist
    if partition_keys:
        schema_text += "\nPartition Keys:\n"
        for pk in partition_keys:
            comment = f" -- {pk['comment']}" if pk['comment'] else ""
            schema_text += f"- {pk['name']} ({pk['type'].upper()}){comment}\n"
    
    return schema_text

def main():
    """Main execution - fetch schemas for Sentra project tables"""
    
    # Sentra project databases and tables
    targets = [
        ('insurance_db', 'insurance_data'),
    ]
    
    print("🚀 Fetching Sentra Project Database Schemas...")
    print("=" * 80)
    
    all_schemas = {}
    
    for db_name, table_name in targets:
        print(f"\n📋 Fetching: {db_name}.{table_name}")
        
        schema_info = fetch_table_columns(db_name, table_name)
        
        if schema_info and schema_info.get('columns'):
            columns = schema_info['columns']
            partition_keys = schema_info.get('partition_keys', [])
            
            print(f"✅ Found {len(columns)} columns")
            if partition_keys:
                print(f"🔑 Found {len(partition_keys)} partition keys")
            
            all_schemas[f"{db_name}.{table_name}"] = schema_info
            
            # Display table metadata
            print(f"   📊 Table Details:")
            print(f"      Type: {schema_info.get('table_type', 'N/A')}")
            print(f"      Location: {schema_info.get('location', 'N/A')}")
            print(f"      Created: {schema_info.get('create_time', 'N/A')}")
            print(f"      Updated: {schema_info.get('update_time', 'N/A')}")
            
            # Display ALL columns with details
            print(f"   📋 Complete schema for {table_name.upper()}:")
            print("   " + "-" * 70)
            for i, col in enumerate(columns, 1):
                comment_text = f" -- {col['comment']}" if col['comment'] else ""
                print(f"   {i:3d}. {col['name']:<35} ({col['type'].upper():<15}){comment_text}")
            
            # Display partition keys if they exist
            if partition_keys:
                print("   " + "-" * 70)
                print("   🔑 PARTITION KEYS:")
                for i, pk in enumerate(partition_keys, 1):
                    comment_text = f" -- {pk['comment']}" if pk['comment'] else ""
                    print(f"   {i:3d}. {pk['name']:<35} ({pk['type'].upper():<15}){comment_text}")
            
            print("   " + "-" * 70)
        else:
            print("❌ No schema information found")
    
    # Generate prompt-ready schema text
    print("\n" + "=" * 80)
    print("📝 GENERATING PROMPT-READY SCHEMA TEXT")
    print("=" * 80)
    
    prompt_schemas = {}
    for db_name, table_name in targets:
        key = f"{db_name}.{table_name}"
        if key in all_schemas and all_schemas[key].get('columns'):
            prompt_text = generate_prompt_schema(db_name, table_name)
            prompt_schemas[key] = prompt_text
            print(f"✅ Generated schema text for {key}")
        else:
            print(f"❌ Skipped {key} - no schema data")
    
    # Save to files
    with open('sentra_schemas_raw.json', 'w') as f:
        json.dump(all_schemas, f, indent=2)
    
    with open('sentra_schemas_prompt.txt', 'w') as f:
        f.write("# SENTRA PROJECT DATABASE SCHEMAS\n")
        f.write("# Generated from AWS Glue Catalog\n\n")
        
        for key, schema_text in prompt_schemas.items():
            f.write(schema_text + "\n")
    
    print(f"\n💾 Raw schemas saved to: sentra_schemas_raw.json")
    print(f"💾 Prompt-ready schemas saved to: sentra_schemas_prompt.txt")

if __name__ == "__main__":
    main()