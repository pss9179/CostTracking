#!/usr/bin/env python3
"""
Create a test API key for local development.
This script creates a user and API key directly in the database.
"""
import sys
import os
from pathlib import Path

# Add collector to path
collector_path = Path(__file__).parent / "collector"
sys.path.insert(0, str(collector_path))

# Set DATABASE_URL environment variable
os.environ['DATABASE_URL'] = 'sqlite:///./collector.db'
os.chdir(str(collector_path))

from sqlmodel import Session, select, create_engine
from models import User, APIKey
from auth import generate_api_key, hash_api_key, get_key_prefix
from datetime import datetime
from uuid import uuid4

# Create engine directly
engine = create_engine('sqlite:///./collector.db')

def create_test_user_and_key():
    """Create a test user and API key."""
    with Session(engine) as session:
        # Check if test user exists
        statement = select(User).where(User.email == "test@example.com")
        existing_user = session.exec(statement).first()
        
        if existing_user:
            print(f"✅ Test user already exists: {existing_user.email}")
            user = existing_user
        else:
            # Create test user
            user = User(
                id=uuid4(),
                clerk_id="test_user_local",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                subscription_tier="free",
                created_at=datetime.utcnow()
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"✅ Created test user: {user.email}")
        
        # Generate new API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        key_prefix = get_key_prefix(api_key)
        
        # Create API key record
        db_key = APIKey(
            id=uuid4(),
            user_id=user.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name="Test API Key",
            created_at=datetime.utcnow()
        )
        
        session.add(db_key)
        session.commit()
        session.refresh(db_key)
        
        print("\n" + "="*80)
        print("🎉 API KEY CREATED SUCCESSFULLY!")
        print("="*80)
        print(f"\n📋 User: {user.email}")
        print(f"🔑 API Key: {api_key}")
        print(f"📝 Key Name: {db_key.name}")
        print(f"📅 Created: {db_key.created_at}")
        print("\n" + "="*80)
        print("💡 Copy the API key above and use it in your tests!")
        print("   Example:")
        print(f'   export LLMOBSERVE_API_KEY="{api_key}"')
        print("="*80 + "\n")
        
        return api_key

if __name__ == "__main__":
    try:
        create_test_user_and_key()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

