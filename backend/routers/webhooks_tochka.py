"""
Tochka webhooks router.

Tochka sends webhooks as a JWT string (RS256) with Content-Type: text/plain.
Docs: https://developers.tochka.com/docs/tochka-api/opisanie-metodov/vebhuki
Public key (JWK): https://enter.tochka.com/doc/openapi/static/keys/public
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import aiohttp
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import APIRouter, Request

from backend.firestore import get_payment, update_payment_status, update_user_balance
from backend.services.notifications import get_notification_service
from backend.services.tochka import get_tochka_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/tochka", tags=["webhooks"])

TOCHKA_JWK_URL = "https://enter.tochka.com/doc/openapi/static/keys/public"

_cached_public_key: Optional[Any] = None


async def _get_public_key():
    global _cached_public_key
    if _cached_public_key is not None:
        return _cached_public_key

    async with aiohttp.ClientSession() as session:
        async with session.get(TOCHKA_JWK_URL) as resp:
            raw = await resp.text()
            if resp.status != 200:
                raise Exception(f"Failed to fetch Tochka JWK (status {resp.status})")
            jwk = json.loads(raw)

    # jwk may be a dict (single key) or jwks with {"keys":[...]}.
    if isinstance(jwk, dict) and "keys" in jwk and isinstance(jwk["keys"], list) and jwk["keys"]:
        jwk = jwk["keys"][0]

    _cached_public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))
    return _cached_public_key


async def _verify_and_decode_jwt(token: str) -> Dict[str, Any]:
    key = await _get_public_key()
    # We don't validate audience/issuer here because Tochka webhook JWT doesn't provide stable aud/iss guarantees.
    return jwt.decode(token, key=key, algorithms=["RS256"], options={"verify_aud": False})


@router.post("/acquiringInternetPayment")
async def webhook_acquiring_internet_payment(request: Request):
    """
    Webhook for payment links events.

    Expected payload: JWT string in body.
    We handle:
    - status APPROVED -> mark payment completed, add energy, send m17
    - other statuses -> mark payment failed, send m16
    """
    token = (await request.body()).decode("utf-8").strip()
    if not token:
        logger.warning("Empty Tochka webhook body")
        return {"ok": True}

    try:
        claims = await _verify_and_decode_jwt(token)
    except Exception as e:
        logger.error(f"Failed to verify Tochka webhook JWT: {e}", exc_info=True)
        # Tochka retries on non-200; return 200 but log it.
        return {"ok": True}

    webhook_type = claims.get("webhookType")
    status = claims.get("status")
    operation_id = claims.get("operationId")
    amount = claims.get("amount")

    logger.info(
        "Tochka webhook received: "
        f"type={webhook_type} status={status} operationId={operation_id} amount={amount}"
    )

    if webhook_type != "acquiringInternetPayment":
        return {"ok": True}

    # Correlate our payment_id.
    payment_id = claims.get("paymentLinkId") or claims.get("paymentLinkID")  # tolerate casing
    if not payment_id and operation_id:
        try:
            tochka = get_tochka_client()
            op = await tochka.get_payment_operation(operation_id=str(operation_id))
            payment_id = op.get("paymentLinkId") or op.get("paymentLinkID")
        except Exception as e:
            logger.error(f"Failed to fetch Tochka payment operation for correlation: {e}", exc_info=True)

    if not payment_id:
        logger.error("Unable to correlate Tochka webhook to payment_id (missing paymentLinkId)")
        return {"ok": True}

    payment = await get_payment(str(payment_id))
    if not payment:
        logger.error(f"Payment not found for payment_id={payment_id}")
        return {"ok": True}

    # Idempotency: if already terminal, do nothing.
    if payment.get("status") in {"completed", "failed", "refunded"}:
        logger.info(f"Payment already terminal: id={payment_id} status={payment.get('status')}")
        return {"ok": True}

    telegram_id = int(payment.get("user_id"))
    payment_type = payment.get("type")
    product = payment.get("product")

    notifications = get_notification_service()

    if status == "APPROVED":
        # Mark completed
        await update_payment_status(
            payment_id=str(payment_id),
            status="completed",
            transaction_id=str(operation_id) if operation_id else None,
        )

        # For now we support one_time energy packs (same as current UX).
        if payment_type == "one_time":
            from backend.routers.payments import GENERATION_PACKS

            pack = next((p for p in GENERATION_PACKS if p["id"] == product), None)
            if pack:
                updated = await update_user_balance(telegram_id, pack["energy"])
                new_balance = updated.get("balance", 0) if updated else pack["energy"]
                await notifications.notify_pack_purchase_success(
                    telegram_id=telegram_id,
                    energy_amount=pack["energy"],
                    new_balance=new_balance,
                )
        return {"ok": True}

    # Not approved -> failed
    await update_payment_status(
        payment_id=str(payment_id),
        status="failed",
        transaction_id=str(operation_id) if operation_id else None,
        error_message=f"Tochka status={status}",
    )
    await notifications.notify_payment_failed(telegram_id=telegram_id, reason=f"Tochka status={status}")
    return {"ok": True}

