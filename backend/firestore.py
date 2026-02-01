"""
Firestore database module for Cloud Run deployment
"""
from google.cloud import firestore
from google.cloud.firestore_v1 import AsyncClient
from datetime import datetime
from typing import Optional, Dict, Any, List
import asyncio


# Firestore async client
_db: Optional[AsyncClient] = None


def get_db() -> AsyncClient:
    """Get Firestore async client (singleton)"""
    global _db
    if _db is None:
        _db = firestore.AsyncClient()
    return _db


# ==================== User Operations ====================

async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram_id"""
    db = get_db()
    doc = await db.collection("users").document(str(telegram_id)).get()
    if doc.exists:
        data = doc.to_dict()
        data["telegram_id"] = int(doc.id)
        return data
    return None


async def create_user(telegram_id: int, username: Optional[str] = None) -> Dict[str, Any]:
    """Create a new user or return existing one"""
    db = get_db()
    doc_ref = db.collection("users").document(str(telegram_id))
    
    # Check if user exists
    doc = await doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        data["telegram_id"] = int(doc.id)
        return data
    
    # Create new user
    user_data = {
        "username": username,
        "plan": "free",
        "balance": 3,  # Free tier starts with 3 generations
        "created_at": datetime.utcnow()
    }
    
    await doc_ref.set(user_data)
    user_data["telegram_id"] = telegram_id
    return user_data


async def update_user_balance(telegram_id: int, amount: int) -> Optional[Dict[str, Any]]:
    """
    Update user balance by adding amount (can be negative for deduction)
    Returns updated user or None if insufficient balance
    """
    db = get_db()
    doc_ref = db.collection("users").document(str(telegram_id))
    
    # Use transaction for atomic update
    @firestore.async_transactional
    async def update_in_transaction(transaction, doc_ref):
        doc = await doc_ref.get(transaction=transaction)
        if not doc.exists:
            return None
        
        current_balance = doc.get("balance") or 0
        new_balance = current_balance + amount
        
        if new_balance < 0:
            return None  # Insufficient balance
        
        transaction.update(doc_ref, {"balance": new_balance})
        
        data = doc.to_dict()
        data["balance"] = new_balance
        data["telegram_id"] = int(doc.id)
        return data
    
    transaction = db.transaction()
    return await update_in_transaction(transaction, doc_ref)


async def update_user_plan(telegram_id: int, plan: str, bonus_generations: int = 0) -> Optional[Dict[str, Any]]:
    """Update user plan and optionally add bonus generations"""
    db = get_db()
    doc_ref = db.collection("users").document(str(telegram_id))
    
    doc = await doc_ref.get()
    if not doc.exists:
        return None
    
    update_data = {"plan": plan}
    if bonus_generations > 0:
        current_balance = doc.get("balance") or 0
        update_data["balance"] = current_balance + bonus_generations
    
    await doc_ref.update(update_data)
    
    updated_doc = await doc_ref.get()
    data = updated_doc.to_dict()
    data["telegram_id"] = int(updated_doc.id)
    return data


# ==================== Generation Operations ====================

async def create_generation(
    telegram_id: int,
    style_id: str,
    mode: str = "normal",
    photo_count: int = 1
) -> Dict[str, Any]:
    """Create a new generation record"""
    db = get_db()
    
    generation_data = {
        "user_id": str(telegram_id),
        "style_id": style_id,
        "mode": mode,
        "photo_count": photo_count,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    # Add document with auto-generated ID
    doc_ref = await db.collection("generations").add(generation_data)
    generation_data["id"] = doc_ref[1].id
    return generation_data


async def update_generation_status(generation_id: str, status: str) -> bool:
    """Update generation status"""
    db = get_db()
    doc_ref = db.collection("generations").document(generation_id)
    
    doc = await doc_ref.get()
    if not doc.exists:
        return False
    
    await doc_ref.update({"status": status})
    return True


async def get_user_generations(telegram_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's generation history"""
    db = get_db()
    
    query = (
        db.collection("generations")
        .where("user_id", "==", str(telegram_id))
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    
    docs = await query.get()
    
    generations = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        generations.append(data)
    
    return generations


# ==================== Pending Style Selection Operations ====================

async def set_pending_style_selection(
    telegram_id: int,
    style_id: str,
    style_name: str,
    photo_count: int = 1,
    mode: str = "normal"
) -> bool:
    """Save pending style selection for a user (used when API approach is needed)"""
    db = get_db()
    doc_ref = db.collection("pending_selections").document(str(telegram_id))
    
    await doc_ref.set({
        "style_id": style_id,
        "style_name": style_name,
        "photo_count": photo_count,
        "mode": mode,
        "created_at": datetime.utcnow()
    })
    return True


async def get_pending_style_selection(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get pending style selection for a user"""
    db = get_db()
    doc = await db.collection("pending_selections").document(str(telegram_id)).get()
    
    if doc.exists:
        return doc.to_dict()
    return None


async def clear_pending_style_selection(telegram_id: int) -> bool:
    """Clear pending style selection for a user"""
    db = get_db()
    doc_ref = db.collection("pending_selections").document(str(telegram_id))
    
    doc = await doc_ref.get()
    if doc.exists:
        await doc_ref.delete()
        return True
    return False