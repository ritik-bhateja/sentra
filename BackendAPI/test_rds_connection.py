"""
Quick test script to verify RDS connection and API functionality
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("\n1️⃣  Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("   ✅ Health check passed:", response.json())
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_create_session():
    """Test creating a session"""
    print("\n2️⃣  Testing session creation...")
    try:
        session_id = f"{int(datetime.now().timestamp() * 1000)}_TEST123456789012345"
        payload = {
            "session_id": session_id,
            "user_id": "test_user",
            "title": "Test Session"
        }
        response = requests.post(f"{API_BASE}/api/sessions", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Session created: {data['id']}")
            return session_id
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def test_get_sessions(user_id):
    """Test getting user sessions"""
    print("\n3️⃣  Testing get user sessions...")
    try:
        response = requests.get(f"{API_BASE}/api/sessions/{user_id}")
        if response.status_code == 200:
            sessions = response.json()
            print(f"   ✅ Found {len(sessions)} session(s)")
            for session in sessions:
                print(f"      - {session['title']} (ID: {session['id'][:20]}...)")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_save_message(session_id):
    """Test saving a message"""
    print("\n4️⃣  Testing save message...")
    try:
        message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
        payload = {
            "message_id": message_id,
            "session_id": session_id,
            "message_type": "user",
            "content": "Hello, this is a test message!",
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        response = requests.post(f"{API_BASE}/api/messages", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Message saved: {data['id']}")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_get_messages(session_id):
    """Test getting session messages"""
    print("\n5️⃣  Testing get session messages...")
    try:
        response = requests.get(f"{API_BASE}/api/sessions/{session_id}/messages")
        if response.status_code == 200:
            messages = response.json()
            print(f"   ✅ Found {len(messages)} message(s)")
            for msg in messages:
                print(f"      - [{msg['type']}] {str(msg['content'])[:50]}...")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_update_session(session_id):
    """Test updating session title"""
    print("\n6️⃣  Testing update session title...")
    try:
        payload = {"title": "Updated Test Session"}
        response = requests.put(f"{API_BASE}/api/sessions/{session_id}", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Session updated: {data['title']}")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_delete_session(session_id):
    """Test deleting a session"""
    print("\n7️⃣  Testing delete session...")
    try:
        response = requests.delete(f"{API_BASE}/api/sessions/{session_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Session deleted: {data['message']}")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("RDS Chat History API - Integration Test")
    print("=" * 60)
    print("\n⚠️  Make sure the API server is running:")
    print("   python Agent_Trigger.py")
    print()
    input("Press Enter to start tests...")
    
    # Run tests
    if not test_health():
        print("\n❌ Health check failed. Is the server running?")
        return
    
    session_id = test_create_session()
    if not session_id:
        print("\n❌ Session creation failed. Check database connection.")
        return
    
    test_get_sessions("test_user")
    test_save_message(session_id)
    test_get_messages(session_id)
    test_update_session(session_id)
    test_delete_session(session_id)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
