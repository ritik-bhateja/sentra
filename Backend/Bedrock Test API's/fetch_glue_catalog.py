#!/usr/bin/env python3
"""
AWS Glue Catalog Schema Fetcher
Fetches database schema information from AWS Glue Data Catalog
"""

import boto3
import json
import logging
from typing import Dict, List, Any
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

class GlueCatalogFetcher:
    """Fetches schema information from AWS Glue Data Catalog"""
    
    def __init__(self, region_name: str = 'ap-south-1'):
        """
        Initialize Glue client
        
        Args:
            region_name: AWS region (default: ap-south-1 for Mumbai)
        """
        try:
            self.glue_client = boto3.client('glue', region_name=region_name)
            self.region = region_name
            logger.info(f"✅ Initialized Glue client for region: {region_name}")
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found. Please configure credentials.")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize Glue client: {str(e)}")
            raise

    def get_databases(self) -> List[Dict[str, Any]]:
        """
        Fetch all databases from Glue Catalog
        
        Returns:
            List of database information
        """
        try:
            logger.info("🔍 Fetching databases from Glue Catalog...")
            
            databases = []
            paginator = self.glue_client.get_paginator('get_databases')
            
            for page in paginator.paginate():
                for db in page['DatabaseList']:
                    databases.append({
                        'name': db['Name'],
                        'description': db.get('Description', ''),
                        'location_uri': db.get('LocationUri', ''),
                        'parameters': db.get('Parameters', {}),
                        'create_time': str(db.get('CreateTime', ''))
                    })
            
            logger.info(f"✅ Found {len(databases)} databases")
            return databases
            
        except ClientError as e:
            logger.error(f"❌ AWS API error fetching databases: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching databases: {e}")
            raise

    def get_tables(self, database_name: str) -> List[Dict[str, Any]]:
        """
        Fetch all tables from a specific database
        
        Args:
            database_name: Name of the database
            
        Returns:
            List of table information
        """
        try:
            logger.info(f"🔍 Fetching tables from database: {database_name}")
            
            tables = []
            paginator = self.glue_client.get_paginator('get_tables')
            
            for page in paginator.paginate(DatabaseName=database_name):
                for table in page['TableList']:
                    tables.append({
                        'name': table['Name'],
                        'database_name': table['DatabaseName'],
                        'owner': table.get('Owner', ''),
                        'create_time': str(table.get('CreateTime', '')),
                        'update_time': str(table.get('UpdateTime', '')),
                        'last_access_time': str(table.get('LastAccessTime', '')),
                        'storage_descriptor': table.get('StorageDescriptor', {}),
                        'partition_keys': table.get('PartitionKeys', []),
                        'table_type': table.get('TableType', ''),
                        'parameters': table.get('Parameters', {})
                    })
            
            logger.info(f"✅ Found {len(tables)} tables in {database_name}")
            return tables
            
        except ClientError as e:
            logger.error(f"❌ AWS API error fetching tables from {database_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching tables from {database_name}: {e}")
            raise

    def get_table_schema(self, database_name: str, table_name: str) -> Dict[str, Any]:
        """
        Fetch detailed schema for a specific table
        
        Args:
            database_name: Name of the database
            table_name: Name of the table
            
        Returns:
            Detailed table schema information
        """
        try:
            logger.info(f"🔍 Fetching schema for table: {database_name}.{table_name}")
            
            response = self.glue_client.get_table(
                DatabaseName=database_name,
                Name=table_name
            )
            
            table = response['Table']
            storage_descriptor = table.get('StorageDescriptor', {})
            
            # Extract column information
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
            
            schema_info = {
                'database_name': database_name,
                'table_name': table_name,
                'columns': columns,
                'partition_keys': partition_keys,
                'location': storage_descriptor.get('Location', ''),
                'input_format': storage_descriptor.get('InputFormat', ''),
                'output_format': storage_descriptor.get('OutputFormat', ''),
                'serde_info': storage_descriptor.get('SerdeInfo', {}),
                'table_type': table.get('TableType', ''),
                'parameters': table.get('Parameters', {}),
                'create_time': str(table.get('CreateTime', '')),
                'update_time': str(table.get('UpdateTime', ''))
            }
            
            logger.info(f"✅ Retrieved schema for {database_name}.{table_name} with {len(columns)} columns")
            return schema_info
            
        except ClientError as e:
            logger.error(f"❌ AWS API error fetching schema for {database_name}.{table_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching schema for {database_name}.{table_name}: {e}")
            raise

    def get_complete_catalog_info(self, target_databases: List[str] = None) -> Dict[str, Any]:
        """
        Fetch complete catalog information for specified databases
        
        Args:
            target_databases: List of database names to fetch (None for all)
            
        Returns:
            Complete catalog information
        """
        try:
            logger.info("🚀 Starting complete catalog fetch...")
            
            catalog_info = {
                'region': self.region,
                'fetch_timestamp': str(boto3.Session().region_name),
                'databases': {}
            }
            
            # Get all databases
            all_databases = self.get_databases()
            
            # Filter databases if specified
            if target_databases:
                databases_to_process = [db for db in all_databases if db['name'] in target_databases]
                logger.info(f"🎯 Processing {len(databases_to_process)} target databases: {target_databases}")
            else:
                databases_to_process = all_databases
                logger.info(f"📊 Processing all {len(databases_to_process)} databases")
            
            # Process each database
            for db_info in databases_to_process:
                db_name = db_info['name']
                logger.info(f"📂 Processing database: {db_name}")
                
                catalog_info['databases'][db_name] = {
                    'info': db_info,
                    'tables': {}
                }
                
                # Get tables for this database
                tables = self.get_tables(db_name)
                
                # Get schema for each table
                for table_info in tables:
                    table_name = table_info['name']
                    logger.info(f"📋 Processing table: {db_name}.{table_name}")
                    
                    try:
                        schema = self.get_table_schema(db_name, table_name)
                        catalog_info['databases'][db_name]['tables'][table_name] = {
                            'basic_info': table_info,
                            'schema': schema
                        }
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to get schema for {db_name}.{table_name}: {e}")
                        catalog_info['databases'][db_name]['tables'][table_name] = {
                            'basic_info': table_info,
                            'schema': None,
                            'error': str(e)
                        }
            
            logger.info("✅ Complete catalog fetch completed successfully")
            return catalog_info
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch complete catalog info: {e}")
            raise

    def save_catalog_to_file(self, catalog_info: Dict[str, Any], filename: str = 'glue_catalog_schema.json'):
        """
        Save catalog information to JSON file
        
        Args:
            catalog_info: Catalog information to save
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(catalog_info, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Catalog information saved to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save catalog to file: {e}")
            raise

def main():
    """Main execution function"""
    try:
        # Initialize fetcher
        fetcher = GlueCatalogFetcher()
        
        # Target databases based on Sentra project
        target_databases = ['insurance_db', 'sentra_db']
        
        logger.info("🎯 Fetching schema for Sentra project databases...")
        
        # Fetch complete catalog info
        catalog_info = fetcher.get_complete_catalog_info(target_databases)
        
        # Save to file
        fetcher.save_catalog_to_file(catalog_info, 'sentra_glue_catalog_schema.json')
        
        # Print summary
        print("\n" + "="*80)
        print("📊 GLUE CATALOG SCHEMA SUMMARY")
        print("="*80)
        
        for db_name, db_data in catalog_info['databases'].items():
            print(f"\n🗄️  Database: {db_name}")
            print(f"   Tables: {len(db_data['tables'])}")
            
            for table_name, table_data in db_data['tables'].items():
                schema = table_data.get('schema')
                if schema:
                    column_count = len(schema.get('columns', []))
                    print(f"   📋 {table_name}: {column_count} columns")
                else:
                    print(f"   📋 {table_name}: Schema unavailable")
        
        print(f"\n✅ Schema information saved to: sentra_glue_catalog_schema.json")
        
    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        raise

if __name__ == "__main__":
    main()