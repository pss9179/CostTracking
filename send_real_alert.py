#!/usr/bin/env python3
"""
Send a real alert email with actual cap data.
"""

import asyncio
import sys
import os

# Add collector to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "collector"))

# Need to set up database URL for Railway
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:example@localhost:5432/llmobserve")

async def main():
    from email_service import send_alert_email
    
    # Your REAL cap data:
    # - Hard Block Cap: $0.010/monthly - $0.219 used (2190% exceeded!)
    # - Alert Only Cap: $0.0015/monthly - $0.219 used (14600% exceeded!)
    
    print("=" * 60)
    print("Sending REAL alert email with actual cap data...")
    print("=" * 60)
    
    # Send Hard Block exceeded alert
    print("\n1. Sending HARD CAP EXCEEDED alert...")
    success = await send_alert_email(
        to_email="ethanzzheng@gmail.com",
        alert_type="cap_exceeded",  # Cap exceeded
        target_type="global",
        target_name="All Services",
        current_spend=0.22,  # Your REAL spend
        cap_limit=0.01,      # Your REAL hard cap limit
        percentage=2190.0,    # Your REAL percentage
        period="monthly",
    )
    print(f"   Result: {'✅ Sent!' if success else '❌ Failed'}")
    
    # Send Soft Cap threshold alert
    print("\n2. Sending SOFT CAP WARNING alert...")
    success = await send_alert_email(
        to_email="ethanzzheng@gmail.com",
        alert_type="threshold_reached",  # Threshold warning
        target_type="global",
        target_name="All Services",
        current_spend=0.22,  # Your REAL spend  
        cap_limit=0.0015,    # Your REAL soft cap limit
        percentage=14600.0,  # Your REAL percentage
        period="monthly",
    )
    print(f"   Result: {'✅ Sent!' if success else '❌ Failed'}")
    
    print("\n" + "=" * 60)
    print("Check ethanzzheng@gmail.com for emails!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

