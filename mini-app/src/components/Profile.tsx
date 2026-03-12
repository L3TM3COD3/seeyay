import { useEffect, useState } from 'react';
import { User, GenerationPack, fetchPacks } from '../api/client';
import { useTelegram } from '../hooks/useTelegram';

interface ProfileProps {
  user: User;
  onEnergyClick: () => void;
}

// Данные пакетов по умолчанию
const defaultPacks: GenerationPack[] = [
  { id: 'pack_10', energy: 10, price: 249, currency: 'RUB' },
  { id: 'pack_50', energy: 50, price: 790, currency: 'RUB' },
  { id: 'pack_120', energy: 120, price: 1290, currency: 'RUB' },
  { id: 'pack_300', energy: 300, price: 2490, currency: 'RUB' },
];

export function Profile({ user, onEnergyClick }: ProfileProps) {
  const [packs, setPacks] = useState<GenerationPack[]>(defaultPacks);
  const { hapticFeedback, user: tgUser } = useTelegram();

  useEffect(() => {
    fetchPacks().then((data) => {
      if (data && data.length > 0) {
        setPacks(data);
      }
    });
  }, []);

  const handlePurchasePack = async (pack: GenerationPack) => {
    hapticFeedback('medium');
    
    if (!tgUser?.id) {
      alert('Ошибка: не удалось определить пользователя');
      return;
    }

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/payments/create-payment-url`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            telegram_id: tgUser.id,
            pack_id: pack.id,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to create payment');
      }

      // Бэкенд создаёт платёж, а сообщение с кнопкой оплаты придёт в чат бота.
      // Здесь просто закрываем мини-апп.
      if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.close();
      }
    } catch (error) {
      console.error('Error creating payment:', error);
      alert('Не удалось создать платеж. Попробуйте позже.');
    }
  };

  return (
    <div className="profile-screen">
      <div className="profile-header">
        <div className="profile-avatar">
          <svg viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="8" r="4" />
            <path d="M12 14c-4 0-8 2-8 6h16c0-4-4-6-8-6z" />
          </svg>
        </div>
        <div className="profile-info">
          <h2 className="profile-name">
            {user.username || `Пользователь ${user.telegram_id}`}
          </h2>
          <p className="profile-id">ID: {user.telegram_id}</p>
        </div>
      </div>

      <div 
        className="profile-balance-block"
        onClick={() => {
          hapticFeedback('light');
          onEnergyClick();
        }}
      >
        <div className="profile-balance-block__left">
          <span className="profile-balance-block__label">Баланс</span>
          <span className="profile-balance-block__energy">{user.balance} ⚡</span>
        </div>
        <div className="profile-balance-block__right">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="profile-balance-block__arrow">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>
      </div>

      <div className="profile-packs">
        <h3 className="profile-packs__title">Купить энергию</h3>
        <div className="profile-packs-grid">
          {packs
            .filter((pack) => !['pack_starter', 'pack_downsell'].includes(pack.id))
            .map((pack) => {
            const badgeMap: Record<string, { text: string; type: string }> = {
              pack_10: { text: 'попробовать', type: 'try' },
              pack_50: { text: 'популярно', type: 'popular' },
              pack_120: { text: 'выгодно', type: 'best' },
              pack_300: { text: 'самый выгодный', type: 'super' },
            };
            const badge = badgeMap[pack.id];
            
            return (
              <div key={pack.id} className="profile-pack-card">
                {badge && (
                  <span className={`profile-pack-card__badge profile-pack-card__badge--${badge.type}`}>
                    {badge.text}
                  </span>
                )}
                <div className="profile-pack-card__header">
                  <span className="profile-pack-card__energy">{pack.energy} ⚡</span>
                </div>
                <div className="profile-pack-card__price">
                  <span className="profile-pack-card__amount">{pack.price} ₽</span>
                </div>
                <button 
                  className="profile-pack-card__button"
                  onClick={() => handlePurchasePack(pack)}
                >
                  Купить
                </button>
              </div>
            );
          })}
        </div>
        <p className="profile-terms">
          Используя бот, вы соглашаетесь с{' '}
          <a href="https://clck.ru/3SPCpi" target="_blank" rel="noopener noreferrer">
            условиями
          </a>
        </p>
      </div>

    </div>
  );
}
