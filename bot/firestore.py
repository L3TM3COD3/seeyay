"""
Firestore client for bot - minimal operations for pending style selections
"""
from google.cloud import firestore
from google.cloud.firestore_v1 import AsyncClient
from typing import Optional, Dict, Any
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
