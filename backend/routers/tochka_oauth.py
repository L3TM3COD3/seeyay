"""
Tochka OAuth bootstrap endpoints.

Reason: Tochka UAPI endpoints require an authorized consent and an Access Token Hybrid.
We create a consent, generate an authorization URL, and handle the redirect callback
to store refresh_token in Firestore. After that, backend can use refresh_token flow.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import aiohttp
from fastapi import APIRouter, HTTPException, Query

from backend.firestore import set_tochka_refresh_token
from backend.services.tochka import TOCHKA_API_BASE, TOCHKA_TOKEN_URL, get_tochka_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tochka/oauth", tags=["tochka-oauth"])


def _redirect_url() -> str:
    # Allow override, otherwise default to production API domain.
    env = os.getenv("TOCHKA_REDIRECT_URL")
    if env:
        return env.strip()
    return "https://seeyay-ai-api-445810320877.europe-west4.run.app/oauth/tochka/callback"


def _authorize_url(consent_id: str, state: str) -> str:
    params = {
        "client_id": get_tochka_client()._get_credentials().client_id,  # internal, but ok for bootstrap
        "response_type": "code",
        "state": state,
        "redirect_uri": _redirect_url(),
        # Tochka expects a space-separated list; we request only what we need.
        "scope": "MakeAcquiringOperation ReadAcquiringData ReadCustomerData ManageWebhookData",
        "consent_id": consent_id,
    }
    return f"https://enter.tochka.com/connect/authorize?{urlencode(params)}"


@router.post("/start")
async def start_oauth() -> Dict[str, Any]:
    """
    Creates a consent and returns an authorization URL.
    User must open that URL and approve access once.
    """
    tochka = get_tochka_client()
    creds = tochka._get_credentials()

    # Create consent using client_credentials (per Tochka docs).
    payload = {
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "grant_type": "client_credentials",
        "scope": "ManageWebhookData",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            TOCHKA_TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            raw = await resp.text()
            if resp.status != 200:
                logger.error(f"Tochka client_credentials failed: status={resp.status} body={raw[:2000]!r}")
                raise HTTPException(status_code=500, detail="Failed to get Tochka tech token")
            token_data = json.loads(raw)

    token = token_data.get("access_token")
    if not token:
        raise HTTPException(status_code=500, detail="Tochka token response missing access_token")

    consent_payload = {
        "Data": {
            "permissions": [
                "ManageWebhookData",
                "MakeAcquiringOperation",
                "ReadAcquiringData",
                "ReadCustomerData",
            ],
            "expirationDateTime": "2030-01-01T00:00:00+00:00",
        }
    }

    url = f"{TOCHKA_API_BASE}/v1.0/consents"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=consent_payload, headers=headers) as resp:
            raw = await resp.text()
            if resp.status != 200:
                logger.error(f"Tochka consent create failed: status={resp.status} body={raw[:2000]!r}")
                raise HTTPException(status_code=500, detail="Failed to create Tochka consent")
            data = json.loads(raw)

    consent_id = (data.get("Data") or {}).get("consentId")
    if not consent_id:
        raise HTTPException(status_code=500, detail="Tochka consent response missing consentId")

    # State can be anything; timestamp is enough for our single-tenant case.
    state = str(int(datetime.now(tz=timezone.utc).timestamp()))

    return {
        "authorize_url": _authorize_url(consent_id=consent_id, state=state),
        "redirect_url": _redirect_url(),
        "client_id": creds.client_id,
    }


@router.get("/callback", include_in_schema=False)
async def oauth_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    This route is not used; kept to avoid confusion if someone hits /api/tochka/oauth/callback.
    """
    raise HTTPException(status_code=404, detail="Use /oauth/tochka/callback")


# Public callback (must match redirect URL in Tochka app registration)
public_router = APIRouter(tags=["tochka-oauth"])


@public_router.get("/oauth/tochka/callback")
async def oauth_redirect_handler(
    code: str = Query(...),
    state: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    Exchanges authorization_code for tokens, stores refresh_token in Firestore,
    and configures the acquiringInternetPayment webhook.
    """
    tochka = get_tochka_client()
    creds = tochka._get_credentials()

    payload = {
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": _redirect_url(),
        "scope": "MakeAcquiringOperation ReadAcquiringData ReadCustomerData ManageWebhookData",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            TOCHKA_TOKEN_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            raw = await resp.text()
            if resp.status != 200:
                logger.error(f"Tochka auth code exchange failed: status={resp.status} body={raw[:2000]!r}")
                raise HTTPException(status_code=500, detail="Failed to exchange Tochka code")
            data = json.loads(raw)

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=500, detail="Tochka token response missing refresh_token")
    if not access_token:
        raise HTTPException(status_code=500, detail="Tochka token response missing access_token")

    # Obtain Access Token Hybrid via introspect.
    introspect_payload = {
        "access_token": access_token,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://enter.tochka.com/connect/introspect",
            data=introspect_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            raw = (await resp.text()).strip()
            if resp.status != 200:
                logger.error(f"Tochka introspect failed: status={resp.status} body={raw[:2000]!r}")
                raise HTTPException(status_code=500, detail="Failed to obtain Tochka Access Token Hybrid")
            hybrid = raw.strip().strip('"')

    await set_tochka_refresh_token(refresh_token, hybrid_token=hybrid)

    # Configure webhook immediately.
    webhook_url = "https://seeyay-ai-api-445810320877.europe-west4.run.app/api/webhooks/tochka/acquiringInternetPayment"
    try:
        await tochka.upsert_webhook(url=webhook_url, webhook_types=["acquiringInternetPayment"])
        webhook_configured = True
    except Exception as e:
        logger.error(f"Failed to configure Tochka webhook after OAuth: {e}", exc_info=True)
        webhook_configured = False

    return {"ok": True, "state": state, "webhook_configured": webhook_configured}


@router.post("/configure-webhook")
async def configure_webhook_manual() -> Dict[str, Any]:
    """
    Manually (re)configure acquiringInternetPayment webhook after OAuth is completed.
    """
    tochka = get_tochka_client()
    webhook_url = "https://seeyay-ai-api-445810320877.europe-west4.run.app/api/webhooks/tochka/acquiringInternetPayment"
    await tochka.upsert_webhook(url=webhook_url, webhook_types=["acquiringInternetPayment"])
    return {"ok": True, "url": webhook_url}

