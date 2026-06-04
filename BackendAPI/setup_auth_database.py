import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")

def setup_auth_database():
    try:
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
        
        print("\nCreating users table...")
        with open('auth_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        print("✅ Users table created successfully!")
        
        cursor.execute("SELECT COUNT(*) FROM users;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Users table has {count} records")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Auth database setup complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Google OAuth2 Authentication - Database Setup")
    print("=" * 60)
    print()
    
    if setup_auth_database():
        print("\n🎉 Ready to start the API server!")
        print("   Run: python Agent_Trigger.py")
    else:
        print("\n⚠️  Please check your configuration and try again")
