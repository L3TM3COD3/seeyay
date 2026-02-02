"""
Notification Service - отправка уведомлений в Telegram
"""
import aiohttp
from typing import Optional
import logging

from backend.secrets import get_bot_token

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """Service for sending Telegram notifications"""
    
    def __init__(self):
        self._bot_token: Optional[str] = None
    
    def _get_bot_token(self) -> str:
        """Get bot token"""
        if not self._bot_token:
            self._bot_token = get_bot_token()
        return self._bot_token
    
    async def send_message(
        self,
        telegram_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[dict] = None
    ) -> bool:
        """Send message to user"""
        try:
            token = self._get_bot_token()
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            
            data = {
                "chat_id": telegram_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                data["reply_markup"] = reply_markup
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info(f"Notification sent to user {telegram_id}")
                        return True
                    else:
                        logger.error(f"Failed to send notification: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending notification to user {telegram_id}: {e}")
            return False
    
    async def notify_pack_purchase_success(
        self,
        telegram_id: int,
        energy_amount: int,
        new_balance: int
    ):
        """Уведомление об успешной покупке пакета энергии"""
        text = (
            f"✅ <b>Оплата прошла успешно!</b>\n\n"
            f"Добавлено: {energy_amount} ⚡\n"
            f"Баланс: {new_balance} ⚡"
        )
        await self.send_message(telegram_id, text)
    
    async def notify_subscription_created(
        self,
        telegram_id: int,
        plan_name: str,
        energy_amount: int,
        new_balance: int
    ):
        """Уведомление о создании подписки"""
        text = (
            f"🎉 <b>Подписка {plan_name} активирована!</b>\n\n"
            f"Добавлено: {energy_amount} ⚡\n"
            f"Баланс: {new_balance} ⚡\n\n"
            f"Подписка будет автоматически продлеваться каждый месяц."
        )
        await self.send_message(telegram_id, text)
    
    async def notify_subscription_renewed(
        self,
        telegram_id: int,
        plan_name: str,
        energy_amount: int,
        new_balance: int
    ):
        """Уведомление о продлении подписки"""
        text = (
            f"✅ <b>Подписка {plan_name} продлена!</b>\n\n"
            f"Добавлено: {energy_amount} ⚡\n"
            f"Баланс: {new_balance} ⚡"
        )
        await self.send_message(telegram_id, text)
    
    async def notify_payment_failed(
        self,
        telegram_id: int,
        reason: str
    ):
        """Уведомление о неудачном платеже"""
        text = (
            f"❌ <b>Оплата не прошла</b>\n\n"
            f"Причина: {reason}\n\n"
            f"Попробуйте еще раз или свяжитесь с поддержкой."
        )
        await self.send_message(telegram_id, text)
    
    async def notify_subscription_grace(
        self,
        telegram_id: int,
        plan_name: str
    ):
        """Уведомление о переходе подписки в grace (неудачное списание)"""
        text = (
            f"⚠️ <b>Не удалось продлить подписку {plan_name}</b>\n\n"
            f"Мы попробуем списать оплату еще раз в ближайшее время.\n"
            f"У вас есть 3 дня (72 часа), чтобы обновить способ оплаты.\n\n"
            f"Доступ к подписке сохраняется."
        )
        
        # Добавляем кнопку для оплаты
        reply_markup = {
            "inline_keyboard": [[
                {"text": "💳 Оплатить подписку", "web_app": {"url": "https://seeyay-miniapp-445810320877.europe-west4.run.app"}}
            ]]
        }
        
        await self.send_message(telegram_id, text, reply_markup=reply_markup)
    
    async def notify_subscription_suspended(
        self,
        telegram_id: int,
        plan_name: str
    ):
        """Уведомление о переходе подписки в suspended"""
        text = (
            f"😔 <b>Не смогли продлить подписку {plan_name}</b>\n\n"
            f"Ваш тариф теперь – Free (1 энергия в сутки).\n\n"
            f"Вы можете возобновить подписку в любой момент."
        )
        
        # Добавляем кнопку для оплаты
        reply_markup = {
            "inline_keyboard": [[
                {"text": "🔄 Возобновить подписку", "web_app": {"url": "https://seeyay-miniapp-445810320877.europe-west4.run.app"}}
            ]]
        }
        
        await self.send_message(telegram_id, text, reply_markup=reply_markup)
    
    async def notify_subscription_expired(
        self,
        telegram_id: int
    ):
        """Уведомление о переходе подписки в expired (со скидкой)"""
        text = (
            f"🎁 <b>Ваша подписка на паузе</b>\n\n"
            f"Специально для вас, её можно возобновить со скидкой на следующий месяц – <b>25%</b>!"
        )
        
        # Добавляем кнопку для оплаты
        reply_markup = {
            "inline_keyboard": [[
                {"text": "🎉 Оплатить подписку (-25%)", "web_app": {"url": "https://seeyay-miniapp-445810320877.europe-west4.run.app"}}
            ]]
        }
        
        await self.send_message(telegram_id, text, reply_markup=reply_markup)
    
    async def notify_subscription_canceled(
        self,
        telegram_id: int
    ):
        """Уведомление об отмене подписки пользователем"""
        text = (
            f"😢 <b>Очень жаль, что вы уходите!</b>\n\n"
            f"Если что, подписку можно возобновить со скидкой на следующий месяц – <b>25%</b>.\n\n"
            f"Неизрасходованная энергия сохранена."
        )
        
        # Добавляем кнопку для оплаты
        reply_markup = {
            "inline_keyboard": [[
                {"text": "🎉 Оплатить подписку (-25%)", "web_app": {"url": "https://seeyay-miniapp-445810320877.europe-west4.run.app"}}
            ]]
        }
        
        await self.send_message(telegram_id, text, reply_markup=reply_markup)
    
    async def notify_insufficient_energy(
        self,
        telegram_id: int,
        current_balance: int
    ):
        """Уведомление о недостаточной энергии"""
        text = (
            f"⚡ <b>Энергия закончилась!</b>\n\n"
            f"Ваш баланс: {current_balance} ⚡\n\n"
            f"Пополните баланс, чтобы продолжить создавать фото."
        )
        
        # Добавляем кнопку для пополнения
        reply_markup = {
            "inline_keyboard": [[
                {"text": "💰 Пополнить баланс", "web_app": {"url": "https://seeyay-miniapp-445810320877.europe-west4.run.app"}}
            ]]
        }
        
        await self.send_message(telegram_id, text, reply_markup=reply_markup)
    
    async def notify_refund(
        self,
        telegram_id: int,
        amount: float
    ):
        """Уведомление о возврате"""
        text = (
            f"💰 <b>Возврат выполнен</b>\n\n"
            f"Сумма: {amount} ₽\n\n"
            f"Средства вернутся на вашу карту в течение 5-10 рабочих дней."
        )
        await self.send_message(telegram_id, text)


# Singleton instance
_service: Optional[TelegramNotificationService] = None


def get_notification_service() -> TelegramNotificationService:
    """Get notification service instance"""
    global _service
    if _service is None:
        _service = TelegramNotificationService()
    return _service
