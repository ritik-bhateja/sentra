"""
Database Setup Script
Run this script to create the database schema in PostgreSQL RDS
"""
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")

def setup_database():
    """Create database tables from schema file"""
    try:
        # Connect to PostgreSQL
        print(f"Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode=DB_SSLMODE
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        
        # Read and execute schema file
        print("\nExecuting database schema...")
        with open('database_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        
        print("✅ Database schema created successfully!")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("\n📊 Tables created:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verify indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY indexname;
        """)
        
        indexes = cursor.fetchall()
        print("\n🔍 Indexes created:")
        for index in indexes:
            print(f"  - {index[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database setup complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Sentra Chat History - Database Setup")
    print("=" * 60)
    print()
    
    success = setup_database()
    
    if success:
        print("\n🎉 You can now start the API server!")
        print("   Run: python Agent_Trigger.py")
    else:
        print("\n⚠️  Please check your .env configuration and try again")
