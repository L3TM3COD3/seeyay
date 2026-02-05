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
        "created_at": datetime.utcnow(),
        "successful_generations": 0,
        "is_new_user": True,
        "starter_pack_purchased": False,
        "m9_shown": False,
        "m7_1_sent": False,
        "m7_2_sent": False,
        "m7_3_sent": False,
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
    mode: str = "normal"
) -> Dict[str, Any]:
    """Create a new generation record"""
    db = get_db()
    
    generation_data = {
        "user_id": str(telegram_id),
        "style_id": style_id,
        "mode": mode,
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
    mode: str = "normal"
) -> bool:
    """Save pending style selection for a user (used when API approach is needed)"""
    db = get_db()
    doc_ref = db.collection("pending_selections").document(str(telegram_id))
    
    await doc_ref.set({
        "style_id": style_id,
        "style_name": style_name,
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


# ==================== Energy Operations ====================

async def deduct_energy(telegram_id: int, amount: int) -> Optional[Dict[str, Any]]:
    """
    Атомарное списание энергии у пользователя
    Returns updated user data or None if insufficient balance
    """
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


async def give_daily_energy(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Начислить ежедневную энергию пользователю на free плане (1 энергия)
    Начисляется только если баланс = 0
    """
    db = get_db()
    doc_ref = db.collection("users").document(str(telegram_id))
    
    doc = await doc_ref.get()
    if not doc.exists:
        return None
    
    user_data = doc.to_dict()
    plan = user_data.get("plan", "free")
    
    # Только для free плана
    if plan != "free":
        return None
    
    # Проверяем баланс - начисляем только если 0
    current_balance = user_data.get("balance", 0)
    if current_balance > 0:
        return None  # Не начисляем если есть энергия
    
    # Обновляем баланс и время последней выдачи
    await doc_ref.update({
        "balance": 1,
        "daily_energy_given_at": datetime.utcnow()
    })
    
    updated_doc = await doc_ref.get()
    data = updated_doc.to_dict()
    data["telegram_id"] = int(updated_doc.id)
    return data


async def get_free_plan_users_for_daily_energy() -> List[Dict[str, Any]]:
    """
    Получить пользователей на free плане для начисления ежедневной энергии
    Только пользователи с balance = 0
    """
    db = get_db()
    
    # Получаем всех пользователей на free плане с нулевым балансом
    query = db.collection("users").where("plan", "==", "free").where("balance", "==", 0)
    docs = await query.get()
    
    users = []
    for doc in docs:
        data = doc.to_dict()
        data["telegram_id"] = int(doc.id)
        users.append(data)
    
    return users


# ==================== Payment Operations ====================

async def create_payment(
    user_id: str,
    payment_type: str,
    product: str,
    amount: float,
    currency: str = "RUB",
    payment_method: str = "card"
) -> Dict[str, Any]:
    """Create a new payment record"""
    db = get_db()
    
    payment_data = {
        "user_id": user_id,
        "type": payment_type,  # one_time | subscription | renewal
        "product": product,
        "amount": amount,
        "currency": currency,
        "status": "pending",
        "cloudpayments_transaction_id": None,
        "payment_method": payment_method,  # card | sbp
        "receipt_url": None,
        "error_message": None,
        "created_at": datetime.utcnow(),
        "completed_at": None
    }
    
    doc_ref = await db.collection("payments").add(payment_data)
    payment_data["id"] = doc_ref[1].id
    return payment_data


async def update_payment_status(
    payment_id: str,
    status: str,
    transaction_id: Optional[str] = None,
    receipt_url: Optional[str] = None,
    error_message: Optional[str] = None
) -> bool:
    """Update payment status"""
    db = get_db()
    doc_ref = db.collection("payments").document(payment_id)
    
    doc = await doc_ref.get()
    if not doc.exists:
        return False
    
    update_data = {
        "status": status,
        "completed_at": datetime.utcnow() if status in ["completed", "failed", "refunded"] else None
    }
    
    if transaction_id:
        update_data["cloudpayments_transaction_id"] = transaction_id
    if receipt_url:
        update_data["receipt_url"] = receipt_url
    if error_message:
        update_data["error_message"] = error_message
    
    await doc_ref.update(update_data)
    return True


async def get_payment(payment_id: str) -> Optional[Dict[str, Any]]:
    """Get payment by ID"""
    db = get_db()
    doc = await db.collection("payments").document(payment_id).get()
    
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


# ==================== Subscription Operations ====================

async def update_subscription(
    telegram_id: int,
    subscription_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update user subscription data"""
    db = get_db()
    doc_ref = db.collection("users").document(str(telegram_id))
    
    doc = await doc_ref.get()
    if not doc.exists:
        return None
    
    await doc_ref.update({"subscription": subscription_data})
    
    updated_doc = await doc_ref.get()
    data = updated_doc.to_dict()
    data["telegram_id"] = int(updated_doc.id)
    return data


async def get_users_for_retry() -> List[Dict[str, Any]]:
    """
    Получить пользователей с подпиской в статусе grace, 
    которым нужен retry платежа
    """
    db = get_db()
    
    # Получаем всех пользователей
    docs = await db.collection("users").get()
    
    users_for_retry = []
    now = datetime.utcnow()
    
    for doc in docs:
        data = doc.to_dict()
        subscription = data.get("subscription")
        
        if not subscription:
            continue
        
        status = subscription.get("status")
        if status != "grace":
            continue
        
        # Проверяем, нужен ли retry
        retry_count = subscription.get("retry_count", 0)
        last_retry_at = subscription.get("last_retry_at")
        
        # Максимум 3 попытки
        if retry_count >= 3:
            continue
        
        # Определяем интервал для следующего retry
        if retry_count == 0:
            # Первый retry через 12 часов
            interval_hours = 12
        elif retry_count == 1:
            # Второй retry через 24 часа после первого
            interval_hours = 24
        else:
            # Третий retry через 48 часов после второго
            interval_hours = 48
        
        # Если last_retry_at пустой, используем grace_ends_at минус 72 часа как начало grace
        if not last_retry_at:
            grace_ends_at = subscription.get("grace_ends_at")
            if grace_ends_at:
                # Первая попытка через 12 часов от начала grace периода
                grace_start = grace_ends_at - firestore.SERVER_TIMESTAMP  # Примерное время начала grace
                if (now - grace_start).total_seconds() >= interval_hours * 3600:
                    data["telegram_id"] = int(doc.id)
                    users_for_retry.append(data)
        else:
            # Проверяем, прошло ли нужное время с последней попытки
            time_since_retry = (now - last_retry_at).total_seconds()
            if time_since_retry >= interval_hours * 3600:
                data["telegram_id"] = int(doc.id)
                users_for_retry.append(data)
    
    return users_for_retry


async def get_expired_grace_users() -> List[Dict[str, Any]]:
    """
    Получить пользователей с истёкшим grace периодом
    """
    db = get_db()
    docs = await db.collection("users").get()
    
    expired_users = []
    now = datetime.utcnow()
    
    for doc in docs:
        data = doc.to_dict()
        subscription = data.get("subscription")
        
        if not subscription:
            continue
        
        status = subscription.get("status")
        grace_ends_at = subscription.get("grace_ends_at")
        
        if status == "grace" and grace_ends_at and now >= grace_ends_at:
            data["telegram_id"] = int(doc.id)
            expired_users.append(data)
    
    return expired_users


async def get_suspended_users_for_expiry() -> List[Dict[str, Any]]:
    """
    Получить пользователей в статусе suspended более 7 дней
    """
    db = get_db()
    docs = await db.collection("users").get()
    
    users_to_expire = []
    now = datetime.utcnow()
    
    for doc in docs:
        data = doc.to_dict()
        subscription = data.get("subscription")
        
        if not subscription:
            continue
        
        status = subscription.get("status")
        grace_ends_at = subscription.get("grace_ends_at")
        
        if status == "suspended" and grace_ends_at:
            # Проверяем, прошло ли 7 дней после окончания grace (т.е. после перехода в suspended)
            days_since_suspended = (now - grace_ends_at).days
            if days_since_suspended >= 7:
                data["telegram_id"] = int(doc.id)
                users_to_expire.append(data)
    
    return users_to_expire