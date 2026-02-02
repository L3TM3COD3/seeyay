"""
Firestore client for bot - minimal operations for pending style selections
"""
from google.cloud import firestore
from google.cloud.firestore_v1 import AsyncClient
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Firestore async client
_db: Optional[AsyncClient] = None


def get_db() -> AsyncClient:
    """Get Firestore async client (singleton)"""
    global _db
    if _db is None:
        _db = firestore.AsyncClient()
    return _db


async def get_pending_style_selection(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get pending style selection for a user"""
    try:
        db = get_db()
        doc = await db.collection("pending_selections").document(str(telegram_id)).get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting pending selection: {e}")
        return None


async def clear_pending_style_selection(telegram_id: int) -> bool:
    """Clear pending style selection for a user"""
    try:
        db = get_db()
        doc_ref = db.collection("pending_selections").document(str(telegram_id))
        
        doc = await doc_ref.get()
        if doc.exists:
            await doc_ref.delete()
            return True
        return False
    except Exception as e:
        logger.error(f"Error clearing pending selection: {e}")
        return False


# ==================== User Operations ====================

async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram_id"""
    try:
        db = get_db()
        doc = await db.collection("users").document(str(telegram_id)).get()
        if doc.exists:
            data = doc.to_dict()
            data["telegram_id"] = int(doc.id)
            return data
        return None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None


async def update_user_balance(telegram_id: int, amount: int) -> Optional[Dict[str, Any]]:
    """
    Update user balance by adding amount (can be negative for deduction)
    Returns updated user or None if insufficient balance
    """
    try:
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
    except Exception as e:
        logger.error(f"Error updating user balance: {e}")
        return None


# ==================== Energy Operations ====================

async def deduct_energy(telegram_id: int, amount: int) -> Optional[Dict[str, Any]]:
    """
    Атомарное списание энергии у пользователя
    Returns updated user data or None if insufficient balance
    """
    try:
        db = get_db()
        doc_ref = db.collection("users").document(str(telegram_id))
        
        @firestore.async_transactional
        async def deduct_in_transaction(transaction, doc_ref):
            doc = await doc_ref.get(transaction=transaction)
            if not doc.exists:
                return None
            
            current_balance = doc.get("balance") or 0
            if current_balance < amount:
                return None  # Insufficient energy
            
            new_balance = current_balance - amount
            transaction.update(doc_ref, {"balance": new_balance})
            
            data = doc.to_dict()
            data["balance"] = new_balance
            data["telegram_id"] = int(doc.id)
            return data
        
        transaction = db.transaction()
        return await deduct_in_transaction(transaction, doc_ref)
    except Exception as e:
        logger.error(f"Error deducting energy: {e}")
        return None
