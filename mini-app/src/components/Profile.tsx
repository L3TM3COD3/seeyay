import { useEffect, useState } from 'react';
import { User, GenerationPack, fetchPacks } from '../api/client';
import { useTelegram } from '../hooks/useTelegram';
import { PaymentModal } from './PaymentModal';

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
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentWidgetParams, setPaymentWidgetParams] = useState<any>(null);
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
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/payments/create-pack-payment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegram_id: tgUser.id,
          pack_id: pack.id
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create payment');
      }

      const data = await response.json();
      setPaymentWidgetParams(data.widget_params);
      setShowPaymentModal(true);
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
          {packs.map((pack) => {
            const badge = pack.id === 'pack_50' ? 'популярно' : pack.id === 'pack_120' ? 'выгодно' : null;
            const badgeType = pack.id === 'pack_50' ? 'popular' : pack.id === 'pack_120' ? 'best' : null;
            const discount = pack.id === 'pack_50' ? '−37%' : pack.id === 'pack_120' ? '−57%' : pack.id === 'pack_300' ? '−67%' : null;
            
            return (
              <div key={pack.id} className="profile-pack-card">
                <div className="profile-pack-card__header">
                  <span className="profile-pack-card__energy">{pack.energy} ⚡</span>
                  {badge && <span className={`profile-pack-card__badge profile-pack-card__badge--${badgeType}`}>{badge}</span>}
                </div>
                <div className="profile-pack-card__price">
                  <span className="profile-pack-card__amount">{pack.price} ₽</span>
                  {discount && <span className="profile-pack-card__discount">{discount}</span>}
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
      </div>

      {/* Payment Modal */}
      <PaymentModal
        isOpen={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        widgetParams={paymentWidgetParams}
        onSuccess={() => {
          alert('Оплата прошла успешно!');
          setShowPaymentModal(false);
          // TODO: Обновить баланс пользователя
        }}
        onFail={(reason) => {
          alert(`Ошибка оплаты: ${reason}`);
          setShowPaymentModal(false);
        }}
      />
    </div>
  );
}
