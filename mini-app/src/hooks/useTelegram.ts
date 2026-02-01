import { useCallback, useEffect, useState } from 'react';

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
}

export function useTelegram() {
  const [isReady, setIsReady] = useState(false);
  const [user, setUser] = useState<TelegramUser | null>(null);

  const tg = typeof window !== 'undefined' ? window.Telegram?.WebApp : null;

  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
      setIsReady(true);

      // Устанавливаем цвета в стиле seeyay.app
      tg.setHeaderColor('#FFFFFF');
      tg.setBackgroundColor('#FFFFFF');

      // Получаем данные пользователя
      if (tg.initDataUnsafe?.user) {
        setUser(tg.initDataUnsafe.user);
      }
    }
  }, [tg]);

  const sendData = useCallback((data: object) => {
    if (tg) {
      try {
        const jsonData = JSON.stringify(data);
        tg.sendData(jsonData);
      } catch (error) {
        console.error('Telegram sendData error:', error);
      }
    }
  }, [tg]);

  const close = useCallback(() => {
    if (tg) {
      tg.close();
    }
  }, [tg]);

  const showBackButton = useCallback((callback: () => void) => {
    if (tg?.BackButton) {
      tg.BackButton.onClick(callback);
      tg.BackButton.show();
    }
  }, [tg]);

  const hideBackButton = useCallback(() => {
    if (tg?.BackButton) {
      tg.BackButton.hide();
    }
  }, [tg]);

  const hapticFeedback = useCallback((type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error') => {
    if (tg?.HapticFeedback) {
      if (['light', 'medium', 'heavy'].includes(type)) {
        tg.HapticFeedback.impactOccurred(type as 'light' | 'medium' | 'heavy');
      } else {
        tg.HapticFeedback.notificationOccurred(type as 'success' | 'warning' | 'error');
      }
    }
  }, [tg]);

  const showMainButton = useCallback((text: string, callback: () => void) => {
    if (tg?.MainButton) {
      tg.MainButton.setText(text);
      tg.MainButton.onClick(callback);
      tg.MainButton.show();
    }
  }, [tg]);

  const hideMainButton = useCallback(() => {
    if (tg?.MainButton) {
      tg.MainButton.hide();
    }
  }, [tg]);

  return {
    tg,
    isReady,
    user,
    sendData,
    close,
    showBackButton,
    hideBackButton,
    showMainButton,
    hideMainButton,
    hapticFeedback,
  };
}
