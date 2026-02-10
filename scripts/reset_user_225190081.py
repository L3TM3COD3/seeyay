"""
DEV ONLY - REMOVE BEFORE PRODUCTION
One-time script to reset user 225190081 to fresh state
Run: python -m scripts.reset_user_225190081
"""
import asyncio
from google.cloud import firestore
from datetime import datetime


async def reset_user():
    db = firestore.AsyncClient()
    user_id = "225190081"
    
    # Delete existing user
    await db.collection("users").document(user_id).delete()
    print(f"[OK] Deleted user {user_id}")
    
    # Create fresh user with all default fields from Plan 1
    await db.collection("users").document(user_id).set({
        "username": "your_username",  # Will be updated on next /start
        "plan": "free",
        "balance": 3,
        "created_at": firestore.SERVER_TIMESTAMP,
        "successful_generations": 0,
        "is_new_user": True,
        "starter_pack_purchased": False,
        "m9_shown": False,
        "m7_1_sent": False,
        "m7_2_sent": False,
        "m7_3_sent": False,
    })
    print(f"[OK] Recreated user {user_id} with fresh defaults:")
    print(f"   - balance: 3 energy")
    print(f"   - successful_generations: 0")
    print(f"   - is_new_user: True")
    print(f"   - All message flags reset to False")
    
    # Close the client (note: close() is not async in newer versions)
    try:
        db.close()
    except:
        pass  # Some versions don't have close() method
    
    print("\n[DONE] User 225190081 is now a fresh new user.")


if __name__ == "__main__":
    asyncio.run(reset_user())
