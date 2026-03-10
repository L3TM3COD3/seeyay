"""
Notification Service - отправка уведомлений в Telegram
"""
import aiohttp
from typing import Optional
import logging

from backend.secrets import get_bot_token
from backend.keyboards_raw import (
    kb_template_grid_raw,
    kb_downsell_raw,
    kb_payment_retry_raw,
    kb_payment_success_raw,
)
from backend.messages import (
    m2_reminder,
    m5_photo_reminder,
    m10_1_tips_after_first,
    m10_2_pro_suggestion,
    m12_downsell,
    m16_payment_cancelled,
    m17_payment_success,
)

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
                        error_text = await response.text()
                        logger.error(f"Failed to send notification to {telegram_id}: {response.status} - {error_text}")
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
        text = m17_payment_success(energy_amount=energy_amount, new_balance=new_balance)
        # URL мини-аппа — тот же, что используется в других уведомлениях
        mini_app_url = "https://seeyay-ai-miniapp-445810320877.europe-west4.run.app"
        keyboard = kb_payment_success_raw(mini_app_url)
        await self.send_message(telegram_id, text, reply_markup=keyboard)
    
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
        # Текст унифицируем под m16 (платёж отменён / не удался)
        text = m16_payment_cancelled()
        keyboard = kb_payment_retry_raw()
        await self.send_message(telegram_id, text, reply_markup=keyboard)
    
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
                {"text": "💳 Оплатить подписку", "web_app": {"url": "https://seeyay-ai-miniapp-445810320877.europe-west4.run.app"}}
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
                {"text": "🔄 Возобновить подписку", "web_app": {"url": "https://seeyay-ai-miniapp-445810320877.europe-west4.run.app"}}
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
                {"text": "🎉 Оплатить подписку (-25%)", "web_app": {"url": "https://seeyay-ai-miniapp-445810320877.europe-west4.run.app"}}
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
                {"text": "🎉 Оплатить подписку (-25%)", "web_app": {"url": "https://seeyay-ai-miniapp-445810320877.europe-west4.run.app"}}
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
                {"text": "💰 Пополнить баланс", "web_app": {"url": "https://seeyay-ai-miniapp-445810320877.europe-west4.run.app"}}
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
    
    # ==================== Delayed Messages (Plan 2) ====================
    
    async def send_m2_reminder(self, telegram_id: int, mini_app_url: str) -> bool:
        """
        m2: Напоминание через 1 час после приветствия (если нет генераций)
        """
        text = m2_reminder()
        keyboard = kb_template_grid_raw(mini_app_url)
        return await self.send_message(telegram_id, text, reply_markup=keyboard)
    
    async def send_m5_photo_reminder(self, telegram_id: int) -> bool:
        """
        m5: Напоминание прислать фото через 7 мин после выбора шаблона
        """
        text = m5_photo_reminder()
        return await self.send_message(telegram_id, text)
    
    async def send_m10_1_tips(self, telegram_id: int, mini_app_url: str) -> bool:
        """
        m10.1: Советы после 1-й генерации (через 60 мин)
        """
        text = m10_1_tips_after_first()
        keyboard = kb_template_grid_raw(mini_app_url)
        return await self.send_message(telegram_id, text, reply_markup=keyboard)
    
    async def send_m10_2_pro_suggestion(self, telegram_id: int, mini_app_url: str) -> bool:
        """
        m10.2: Предложение попробовать PRO (через 60 мин после 2-й генерации)
        """
        text = m10_2_pro_suggestion()
        keyboard = kb_template_grid_raw(mini_app_url)
        return await self.send_message(telegram_id, text, reply_markup=keyboard)
    
    async def send_m12_downsell(self, telegram_id: int) -> bool:
        """
        m12: Пробный пакет (через 24ч после m9 если не купил)
        """
        text = m12_downsell()
        keyboard = kb_downsell_raw()
        return await self.send_message(telegram_id, text, reply_markup=keyboard)


# Singleton instance
_service: Optional[TelegramNotificationService] = None


def get_notification_service() -> TelegramNotificationService:
    """Get notification service instance"""
    global _service
    if _service is None:
        _service = TelegramNotificationService()
    return _service
