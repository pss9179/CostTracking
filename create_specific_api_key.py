#!/usr/bin/env python3
"""
Create a specific API key that matches what the test is using.
"""
import sys
import os
from pathlib import Path

# Add collector to path
collector_path = Path(__file__).parent / "collector"
sys.path.insert(0, str(collector_path))

os.environ['DATABASE_URL'] = 'sqlite:///./collector.db'
os.chdir(str(collector_path))

from sqlmodel import Session, create_engine
from models import User, APIKey
from auth import hash_api_key, get_key_prefix
from datetime import datetime
from uuid import uuid4

# The specific API key from the test
SPECIFIC_KEY = "llmo_sk_bc53e472d0bfe8e50007a4ea8f028d7bcdd15099eab0d634"

engine = create_engine('sqlite:///./collector.db')

with Session(engine) as session:
    # Get or create test user
    from sqlmodel import select
    statement = select(User).where(User.email == "test@example.com")
    user = session.exec(statement).first()
    
    if not user:
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
    else:
        print(f"✅ Using existing user: {user.email}")
    
    # Create the specific API key
    key_hash = hash_api_key(SPECIFIC_KEY)
    key_prefix = get_key_prefix(SPECIFIC_KEY)
    
    db_key = APIKey(
        id=uuid4(),
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name="Test API Key (from error logs)",
        created_at=datetime.utcnow()
    )
    
    session.add(db_key)
    session.commit()
    session.refresh(db_key)
    
    print("\n" + "="*80)
    print("🎉 SPECIFIC API KEY CREATED!")
    print("="*80)
    print(f"\n🔑 API Key: {SPECIFIC_KEY}")
    print(f"📝 Key Name: {db_key.name}")
    print(f"📋 User: {user.email}")
    print("\n✅ This key should now work in your tests!")
    print("="*80 + "\n")

