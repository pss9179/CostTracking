"""
Create a test user and API key for development.
"""
import sys
import os

# Add collector to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'collector'))

from sqlmodel import Session
from db import engine, init_db
from models import User, APIKey
from auth import generate_api_key, hash_api_key, get_key_prefix
from datetime import datetime

def create_test_user():
    """Create a test user with an API key."""
    
    # Initialize database
    init_db()
    
    with Session(engine) as session:
        # Check if test user already exists
        from sqlmodel import select
        statement = select(User).where(User.email == "test@example.com")
        existing = session.exec(statement).first()
        
        if existing:
            print(f"✅ Test user already exists: {existing.email}")
            print(f"   User ID: {existing.id}")
            
            # Get their API keys
            api_keys_stmt = select(APIKey).where(
                APIKey.user_id == existing.id,
                APIKey.revoked_at.is_(None)
            )
            api_keys = session.exec(api_keys_stmt).all()
            
            if api_keys:
                print(f"\n🔑 Existing API Keys:")
                for key in api_keys:
                    print(f"   - {key.name}: {key.key_prefix}...")
                print(f"\n⚠️  Cannot show full keys (they're hashed).")
                print(f"   Generate a new one with: POST http://localhost:8000/api-keys")
            else:
                print(f"\n⚠️  No API keys found. Creating one...")
                # Create API key
                api_key_plain = generate_api_key()
                key_hash = hash_api_key(api_key_plain)
                key_prefix = get_key_prefix(api_key_plain)
                
                api_key_obj = APIKey(
                    user_id=existing.id,
                    key_hash=key_hash,
                    key_prefix=key_prefix,
                    name="Test API Key"
                )
                session.add(api_key_obj)
                session.commit()
                
                print(f"\n🔑 New API Key Created:")
                print(f"   Name: Test API Key")
                print(f"   Key: {api_key_plain}")
                print(f"\n⚠️  Save this key! It won't be shown again.")
            
            return existing.id
        
        # Create new test user
        user = User(
            clerk_user_id="test_clerk_123",
            email="test@example.com",
            name="Test User"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"✅ Created test user: {user.email}")
        print(f"   User ID: {user.id}")
        
        # Generate API key
        api_key_plain = generate_api_key()
        key_hash = hash_api_key(api_key_plain)
        key_prefix = get_key_prefix(api_key_plain)
        
        api_key_obj = APIKey(
            user_id=user.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name="Test API Key"
        )
        session.add(api_key_obj)
        session.commit()
        
        print(f"\n🔑 API Key Generated:")
        print(f"   Name: Test API Key")
        print(f"   Key: {api_key_plain}")
        print(f"\n⚠️  Save this key! It won't be shown again.")
        print(f"\n📝 Test with:")
        print(f"   curl -H 'Authorization: Bearer {api_key_plain}' http://localhost:8000/runs/latest")
        
        return user.id

if __name__ == "__main__":
    create_test_user()

