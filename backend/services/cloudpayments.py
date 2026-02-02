"""
CloudPayments API Client
https://developers.cloudpayments.ru/#api
"""
import aiohttp
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from backend.secrets import get_secret

logger = logging.getLogger(__name__)


class CloudPaymentsClient:
    """Client for CloudPayments API"""
    
    def __init__(self):
        self.api_url = "https://api.cloudpayments.ru"
        self._public_id: Optional[str] = None
        self._api_secret: Optional[str] = None
    
    async def _get_credentials(self):
        """Get CloudPayments credentials from Secret Manager"""
        if not self._public_id or not self._api_secret:
            try:
                self._public_id = get_secret("cloudpayments-public-id")
                self._api_secret = get_secret("cloudpayments-api-secret")
            except Exception as e:
                logger.error(f"Failed to get CloudPayments credentials: {e}")
                raise
        return self._public_id, self._api_secret
    
    async def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make authenticated request to CloudPayments API"""
        public_id, api_secret = await self._get_credentials()
        
        # Basic Auth
        auth = aiohttp.BasicAuth(public_id, api_secret)
        
        url = f"{self.api_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, auth=auth) as response:
                result = await response.json()
                
                if not result.get("Success"):
                    error_message = result.get("Message", "Unknown error")
                    logger.error(f"CloudPayments API error: {error_message}")
                    raise Exception(f"CloudPayments API error: {error_message}")
                
                return result
    
    async def charge_token(
        self,
        amount: float,
        currency: str,
        account_id: str,
        token: str,
        description: str,
        invoice_id: str,
        email: Optional[str] = None,
        receipt: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Рекуррентный платёж по токену
        https://developers.cloudpayments.ru/#oplata-po-tokenu-rekkarring
        """
        data = {
            "Amount": amount,
            "Currency": currency,
            "AccountId": account_id,
            "Token": token,
            "Description": description,
            "InvoiceId": invoice_id,
        }
        
        if email:
            data["Email"] = email
        
        if receipt:
            data["CloudPayments"] = {"CustomerReceipt": receipt}
        
        return await self._make_request("/payments/tokens/charge", data)
    
    async def create_sbp_qr(
        self,
        amount: float,
        account_id: str,
        description: str,
        invoice_id: str,
        email: Optional[str] = None,
        receipt: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Получение QR-кода для оплаты по СБП
        https://developers.cloudpayments.ru/#sbp
        """
        public_id, _ = await self._get_credentials()
        
        data = {
            "publicId": public_id,
            "amount": amount,
            "accountId": account_id,
            "description": description,
            "invoiceId": invoice_id,
            "ttl": 600,  # 10 минут
        }
        
        if email:
            data["email"] = email
        
        if receipt:
            data["receipt"] = receipt
        
        # СБП использует отдельный эндпоинт без аутентификации
        url = f"{self.api_url}/payments/qr/sbp/create"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                
                if not result.get("success"):
                    error_message = result.get("message", "Unknown error")
                    logger.error(f"CloudPayments SBP QR error: {error_message}")
                    raise Exception(f"CloudPayments SBP QR error: {error_message}")
                
                return result
    
    async def refund(
        self,
        transaction_id: int,
        amount: float
    ) -> Dict[str, Any]:
        """
        Возврат денег
        https://developers.cloudpayments.ru/#vozvrat-deneg
        """
        data = {
            "TransactionId": transaction_id,
            "Amount": amount
        }
        
        return await self._make_request("/payments/refund", data)
    
    async def get_transaction(
        self,
        transaction_id: int
    ) -> Dict[str, Any]:
        """
        Просмотр транзакции
        https://developers.cloudpayments.ru/#prosmotr-tranzaktsii
        """
        data = {
            "TransactionId": transaction_id
        }
        
        return await self._make_request("/payments/get", data)
    
    def verify_notification(
        self,
        data: str,
        signature: str
    ) -> bool:
        """
        Проверка подлинности уведомления
        https://developers.cloudpayments.ru/#proverka-uvedomleniy
        """
        try:
            _, api_secret = self._get_credentials()
            
            # Вычисляем HMAC-SHA256
            message = data.encode('utf-8')
            secret = api_secret.encode('utf-8')
            computed_signature = base64.b64encode(
                hmac.new(secret, message, hashlib.sha256).digest()
            ).decode('utf-8')
            
            return hmac.compare_digest(computed_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying notification: {e}")
            return False
    
    def generate_widget_params(
        self,
        amount: float,
        currency: str,
        description: str,
        invoice_id: str,
        account_id: str,
        email: Optional[str] = None,
        require_confirmation: bool = False,
        receipt: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Генерация параметров для CloudPayments виджета
        """
        params = {
            "publicId": self._public_id,
            "description": description,
            "amount": amount,
            "currency": currency,
            "invoiceId": invoice_id,
            "accountId": account_id,
            "requireConfirmation": require_confirmation,
        }
        
        if email:
            params["email"] = email
        
        if receipt:
            params["data"] = {
                "CloudPayments": {
                    "CustomerReceipt": receipt
                }
            }
        
        return params


# Singleton instance
_client: Optional[CloudPaymentsClient] = None


def get_cloudpayments_client() -> CloudPaymentsClient:
    """Get CloudPayments client instance"""
    global _client
    if _client is None:
        _client = CloudPaymentsClient()
    return _client


def create_receipt(
    items: list,
    email: str,
    taxation_system: int = 1,
) -> Dict[str, Any]:
    """
    Создание чека для онлайн-кассы (54-ФЗ)
    https://developers.cloudpayments.ru/#format-peredachi-dannyh-dlya-onlayn-cheka
    
    Args:
        items: Список товаров/услуг
        email: Email покупателя
        taxation_system: Система налогообложения (1 - ОСН, 2 - УСН доход и т.д.)
    """
    return {
        "Items": items,
        "email": email,
        "taxationSystem": taxation_system,
    }


def create_receipt_item(
    label: str,
    price: float,
    quantity: float = 1.0,
    amount: float = None,
    vat: int = 0,
    method: int = 4,  # 4 - полная оплата
    object_type: int = 4,  # 4 - услуга
) -> Dict[str, Any]:
    """
    Создание позиции чека
    
    Args:
        label: Наименование товара/услуги
        price: Цена за единицу
        quantity: Количество
        amount: Сумма (если не указана, рассчитывается как price * quantity)
        vat: НДС (0 - без НДС, 10, 20 и т.д.)
        method: Признак способа расчета (4 - полная оплата)
        object_type: Признак предмета расчета (4 - услуга)
    """
    if amount is None:
        amount = price * quantity
    
    return {
        "label": label,
        "price": price,
        "quantity": quantity,
        "amount": amount,
        "vat": vat,
        "method": method,
        "object": object_type,
    }
