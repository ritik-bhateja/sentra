"""
Script to add authorized users to the database
Only users in this table can login to the application

When Keycloak is enabled, newly added users are also created in Keycloak
with the default role (viewer_without_query). Keycloak failures are logged
but never block the RDS add operation (Requirements: 3.4, 4.1, 4.4).
"""
import psycopg2
from dotenv import load_dotenv
import os
import sys
import logging

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")

def _sync_to_keycloak(email):
    """Create a Keycloak user with default role after RDS add.

    Failures are logged as warnings but never block the RDS operation.
    Requirements: 3.4, 4.1, 4.4
    """
    try:
        from auth.keycloak_client import KeycloakClient, KeycloakUnavailable
        from auth.roles import DEFAULT_ROLE
    except ImportError as exc:
        logger.warning("Keycloak modules not available, skipping sync: %s", exc)
        return

    client = KeycloakClient()
    if not client.is_enabled():
        return

    try:
        if client.user_exists(email):
            logger.info("Keycloak user already exists for %s, skipping", email)
            return
        user_id = client.create_user(email)
        client.assign_realm_role(user_id, DEFAULT_ROLE)
        print(f"🔑 Created Keycloak user with default role: {email}")
    except KeycloakUnavailable as exc:
        logger.warning("Keycloak sync failed for %s (RDS add still succeeded): %s", email, exc)
        print(f"⚠️  Keycloak sync failed (user still added to RDS): {exc}")
    except Exception as exc:
        logger.warning("Unexpected error during Keycloak sync for %s: %s", email, exc)
        print(f"⚠️  Keycloak sync failed (user still added to RDS): {exc}")


def add_user(email):
    """Add a user to the authorized users list"""
    try:
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
        
        # Check if user already exists
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️  User already exists: {email}")
        else:
            # Insert new user into RDS
            cursor.execute(
                "INSERT INTO users (email) VALUES (%s) RETURNING id, email",
                (email,)
            )
            user = cursor.fetchone()
            print(f"✅ Added authorized user: {user[1]} (ID: {user[0]})")

            # Post-add hook: create Keycloak user with default role (Req 3.4, 4.1, 4.4)
            _sync_to_keycloak(email)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def list_users():
    """List all authorized users"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode=DB_SSLMODE
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, email, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        print("\n📋 Authorized Users:")
        print("-" * 60)
        for user in users:
            print(f"ID: {user[0]:<5} | Email: {user[1]:<40} | Added: {user[2]}")
        print("-" * 60)
        print(f"Total: {len(users)} users")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def remove_user(email):
    """Remove a user from authorized users list"""
    try:
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
        
        cursor.execute("DELETE FROM users WHERE email = %s RETURNING email", (email,))
        deleted = cursor.fetchone()
        
        if deleted:
            print(f"✅ Removed user: {deleted[0]}")
        else:
            print(f"⚠️  User not found: {email}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Sentra - Authorized Users Management")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python add_authorized_user.py add <email>     - Add authorized user")
        print("  python add_authorized_user.py list            - List all users")
        print("  python add_authorized_user.py remove <email>  - Remove user")
        print()
        print("Examples:")
        print("  python add_authorized_user.py add user@gmail.com")
        print("  python add_authorized_user.py list")
        print("  python add_authorized_user.py remove user@gmail.com")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "add":
        if len(sys.argv) < 3:
            print("❌ Error: Email required")
            print("Usage: python add_authorized_user.py add <email>")
            sys.exit(1)
        add_user(sys.argv[2])
    
    elif command == "list":
        list_users()
    
    elif command == "remove":
        if len(sys.argv) < 3:
            print("❌ Error: Email required")
            print("Usage: python add_authorized_user.py remove <email>")
            sys.exit(1)
        remove_user(sys.argv[2])
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: add, list, remove")
        sys.exit(1)
