"""
Tochka Bank API client (payment links + webhooks).

We use:
- OAuth 2.0 client_credentials: https://enter.tochka.com/connect/token
- Payment links: POST https://enter.tochka.com/uapi/acquiring/v1.0/payments
- Webhook management: /webhook/v1.0/{client_id}

Docs:
- https://enter.tochka.com/doc/v2/redoc/section/Authentication
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp

from backend.secrets import get_secret

logger = logging.getLogger(__name__)


TOCHKA_TOKEN_URL = "https://enter.tochka.com/connect/token"
TOCHKA_API_BASE = "https://enter.tochka.com/uapi"
TOCHKA_PAYMENTS_PATH = "/acquiring/v1.0/payments"
TOCHKA_WEBHOOK_PATH_TEMPLATE = "/webhook/v1.0/{client_id}"


def _get_secret_or_env(env_name: str, secret_id: str) -> str:
    val = os.getenv(env_name)
    if val:
        return val.strip()
    return get_secret(secret_id)


@dataclass
class TochkaCredentials:
    client_id: str
    client_secret: str
    customer_code: str
    merchant_id: str


class TochkaClient:
    def __init__(self):
        self._creds: Optional[TochkaCredentials] = None
        self._access_token: Optional[str] = None
        self._access_token_exp: float = 0.0

    def _get_credentials(self) -> TochkaCredentials:
        if self._creds is None:
            self._creds = TochkaCredentials(
                client_id=_get_secret_or_env("TOCHKA_CLIENT_ID", "tochka-client-id"),
                client_secret=_get_secret_or_env("TOCHKA_CLIENT_SECRET", "tochka-client-secret"),
                customer_code=_get_secret_or_env("TOCHKA_CUSTOMER_CODE", "tochka-customer-code"),
                merchant_id=_get_secret_or_env("TOCHKA_MERCHANT_ID", "tochka-merchant-id"),
            )
        return self._creds

    async def get_access_token(self) -> str:
        """
        OAuth2 client_credentials.

        The token endpoint uses application/x-www-form-urlencoded.
        """
        # 30s safety window
        if self._access_token and (time.time() + 30) < self._access_token_exp:
            return self._access_token

        creds = self._get_credentials()

        payload = {
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "grant_type": "client_credentials",
            # Request only the scopes we need for payment links + webhooks.
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
                    logger.error(f"Tochka token request failed: status={resp.status} body={raw[:2000]!r}")
                    raise Exception(f"Tochka token request failed (status {resp.status})")
                data = json.loads(raw)

        token = data.get("access_token")
        if not token:
            raise Exception("Tochka token response missing access_token")

        expires_in = float(data.get("expires_in", 3600))
        self._access_token = token
        self._access_token_exp = time.time() + expires_in
        return token

    async def create_payment_link(
        self,
        *,
        amount_rub: float,
        purpose: str,
        payment_link_id: str,
        payment_modes: List[str],
        ttl_minutes: Optional[int] = None,
        redirect_url: Optional[str] = None,
        fail_redirect_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create payment operation and return Tochka response model.

        Uses Create Payment Operation: POST /acquiring/v1.0/payments
        Request schema (per OpenAPI): {\"Data\": {...}}
        """
        token = await self.get_access_token()
        creds = self._get_credentials()

        data_model: Dict[str, Any] = {
            "customerCode": creds.customer_code,
            "amount": float(amount_rub),
            "purpose": purpose,
            "paymentMode": payment_modes,
            "paymentLinkId": payment_link_id,
        }

        # merchantId is required only when multiple points exist, but passing it is harmless.
        if creds.merchant_id:
            data_model["merchantId"] = creds.merchant_id
        if ttl_minutes is not None:
            data_model["ttl"] = int(ttl_minutes)
        if redirect_url:
            data_model["redirectUrl"] = redirect_url
        if fail_redirect_url:
            data_model["failRedirectUrl"] = fail_redirect_url

        url = f"{TOCHKA_API_BASE}{TOCHKA_PAYMENTS_PATH}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            # Tochka OpenAPI requires company context in header as well.
            "CustomerCode": creds.customer_code,
        }

        payload = {"Data": data_model}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                raw = await resp.text()
                if resp.status != 200:
                    logger.error(f"Tochka create payment failed: status={resp.status} body={raw[:4000]!r}")
                    raise Exception(f"Tochka create payment failed (status {resp.status})")
                return json.loads(raw)

    async def get_payment_operation(self, *, operation_id: str) -> Dict[str, Any]:
        """
        Get Payment Operation Info.

        Endpoint (per OpenAPI): GET /acquiring/v1.0/payments/{operationId}
        """
        token = await self.get_access_token()
        creds = self._get_credentials()

        url = f"{TOCHKA_API_BASE}{TOCHKA_PAYMENTS_PATH}/{operation_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "CustomerCode": creds.customer_code,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                raw = await resp.text()
                if resp.status != 200:
                    logger.error(f"Tochka get payment failed: status={resp.status} body={raw[:4000]!r}")
                    raise Exception(f"Tochka get payment failed (status {resp.status})")
                return json.loads(raw)

    async def upsert_webhook(
        self,
        *,
        url: str,
        webhook_types: List[str],
    ) -> Dict[str, Any]:
        """
        Create or update webhook for this client_id.

        Endpoint (per OpenAPI):
        PUT/POST/GET/DELETE /webhook/v1.0/{client_id}
        """
        token = await self.get_access_token()
        creds = self._get_credentials()

        path = TOCHKA_WEBHOOK_PATH_TEMPLATE.format(client_id=creds.client_id)
        full_url = f"{TOCHKA_API_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "CustomerCode": creds.customer_code,
        }
        body = {"webhooksList": webhook_types, "url": url}

        async with aiohttp.ClientSession() as session:
            async with session.put(full_url, json=body, headers=headers) as resp:
                raw = await resp.text()
                if resp.status != 200:
                    logger.error(f"Tochka upsert webhook failed: status={resp.status} body={raw[:4000]!r}")
                    raise Exception(f"Tochka upsert webhook failed (status {resp.status})")
                return json.loads(raw)


_client: Optional[TochkaClient] = None


def get_tochka_client() -> TochkaClient:
    global _client
    if _client is None:
        _client = TochkaClient()
    return _client

