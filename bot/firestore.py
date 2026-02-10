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


async def increment_successful_generations(telegram_id: int) -> Optional[int]:
    """
    Атомарное увеличение счётчика успешных генераций
    Returns new count or None on error
    """
    try:
        db = get_db()
        doc_ref = db.collection("users").document(str(telegram_id))
        
        @firestore.async_transactional
        async def increment_in_transaction(transaction, doc_ref):
            doc = await doc_ref.get(transaction=transaction)
            if not doc.exists:
                return None
            
            current_count = doc.get("successful_generations") or 0
            new_count = current_count + 1
            transaction.update(doc_ref, {"successful_generations": new_count})
            return new_count
        
        transaction = db.transaction()
        return await increment_in_transaction(transaction, doc_ref)
    except Exception as e:
        logger.error(f"Error incrementing successful_generations: {e}")
        return None


async def set_user_flag(telegram_id: int, flag_name: str, value: bool) -> bool:
    """
    Установить флаг пользователя (например m9_shown, m7_1_sent и т.д.)
    Returns True on success, False on error
    """
    try:
        db = get_db()
        doc_ref = db.collection("users").document(str(telegram_id))
        await doc_ref.update({flag_name: value})
        return True
    except Exception as e:
        logger.error(f"Error setting user flag {flag_name}: {e}")
        return False


async def set_user_timestamp(telegram_id: int, field: str, value: datetime) -> bool:
    """
    Установить timestamp поля пользователя (например started_at, template_selected_at и т.д.)
    Returns True on success, False on error
    """
    try:
        db = get_db()
        doc_ref = db.collection("users").document(str(telegram_id))
        await doc_ref.update({field: value})
        return True
    except Exception as e:
        logger.error(f"Error setting user timestamp {field}: {e}")
        return False


async def ensure_user_exists(telegram_id: int, username: Optional[str] = None) -> Dict[str, Any]:
    """
    Проверить существование пользователя, создать если не существует
    Returns user data
    """
    try:
        db = get_db()
        doc_ref = db.collection("users").document(str(telegram_id))
        doc = await doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            data["telegram_id"] = int(doc.id)
            return data
        
        # Create new user with all default fields
        user_data = {
            "username": username,
            "plan": "free",
            "balance": 3,
            "created_at": datetime.utcnow(),
            "successful_generations": 0,
            "is_new_user": True,
            "starter_pack_purchased": False,
            "m9_shown": False,
            "m7_1_sent": False,
            "m7_2_sent": False,
            "m7_3_sent": False,
            # Delayed messages fields (Plan 2)
            "started_at": None,
            "template_selected_at": None,
            "last_generation_at": None,
            "m2_sent": False,
            "m5_sent": False,
            "m10_1_sent": False,
            "m10_2_sent": False,
            "m12_sent": False,
            "m9_sent_at": None,
            "any_pack_purchased": False,
        }
        
        await doc_ref.set(user_data)
        user_data["telegram_id"] = telegram_id
        return user_data
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}")
        return None
