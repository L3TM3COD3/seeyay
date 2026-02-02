import { useEffect, useState } from 'react';
import { GenerationPack, fetchPacks } from '../api/client';
import { useTelegram } from '../hooks/useTelegram';
import { PaymentModal } from '../components/PaymentModal';

interface EnergyPageProps {
  currentPlan: string;
}

interface Tariff {
  id: string;
  name: string;
  price: string;
  priceValue: number;
  energy: string;
  description: string;
  badge?: {
    text: string;
    type: 'popular' | 'best';
  };
}

const tariffs: Tariff[] = [
  {
    id: 'free',
    name: 'Free',
    price: '0 ₽',
    priceValue: 0,
    energy: '1 ⚡ / день',
    description: '1 энергия в сутки, обновляется каждый день в 00:00 по МСК',
  },
  {
    id: 'basic',
    name: 'Basic',
    price: '499 ₽',
    priceValue: 499,
    energy: '30 ⚡ / месяц',
    description: '30 энергии в месяц, обновляются при следующей оплате',
    badge: {
      text: 'Популярный',
      type: 'popular',
    },
  },
  {
    id: 'pro',
    name: 'PRO',
    price: '1299 ₽',
    priceValue: 1299,
    energy: '150 ⚡ / месяц',
    description: '150 энергии в месяц, обновляются при следующей оплате',
    badge: {
      text: 'Выгодный',
      type: 'best',
    },
  },
];

// Начальные данные для мгновенного отображения
const defaultPacks: GenerationPack[] = [
  { id: 'pack_10', energy: 10, price: 99, currency: 'RUB' },
  { id: 'pack_30', energy: 30, price: 249, currency: 'RUB' },
  { id: 'pack_100', energy: 100, price: 699, currency: 'RUB' },
];

export function EnergyPage({ currentPlan }: EnergyPageProps) {
  const [packs, setPacks] = useState<GenerationPack[]>(defaultPacks);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentWidgetParams, setPaymentWidgetParams] = useState<any>(null);
  const [showSBP, setShowSBP] = useState(false);
  const [sbpData, setSBPData] = useState<{qr_url: string; deeplink: string} | null>(null);
  const { hapticFeedback, user } = useTelegram();

  useEffect(() => {
    fetchPacks().then((data) => {
      if (data && data.length > 0) {
        setPacks(data);
      }
    });
  }, []);

  const handlePurchasePack = async (pack: GenerationPack) => {
    hapticFeedback('medium');
    
    if (!user?.id) {
      alert('Ошибка: не удалось определить пользователя');
      return;
    }

    try {
      // Запрашиваем параметры для виджета
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/payments/create-pack-payment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegram_id: user.id,
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

  const handlePurchasePackSBP = async (pack: GenerationPack) => {
    hapticFeedback('medium');
    
    if (!user?.id) {
      alert('Ошибка: не удалось определить пользователя');
      return;
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/payments/sbp/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegram_id: user.id,
          product_type: 'pack',
          product_id: pack.id
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create SBP payment');
      }

      const data = await response.json();
      setSBPData({ qr_url: data.qr_url, deeplink: data.deeplink });
      setShowSBP(true);
    } catch (error) {
      console.error('Error creating SBP payment:', error);
      alert('Не удалось создать платеж. Попробуйте позже.');
    }
  };

  const handleSelectTariff = async (tariff: Tariff) => {
    hapticFeedback('medium');
    
    if (tariff.id === 'free') {
      alert('Вы уже используете бесплатный тариф');
      return;
    }

    if (!user?.id) {
      alert('Ошибка: не удалось определить пользователя');
      return;
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/payments/create-subscription`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegram_id: user.id,
          plan: tariff.id
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create subscription');
      }

      const data = await response.json();
      
      if (data.discount_applied > 0) {
        alert(`Применена скидка ${data.discount_applied}%!`);
      }
      
      setPaymentWidgetParams(data.widget_params);
      setShowPaymentModal(true);
    } catch (error) {
      console.error('Error creating subscription:', error);
      alert('Не удалось создать подписку. Попробуйте позже.');
    }
  };

  const handleSelectTariffSBP = async (tariff: Tariff) => {
    hapticFeedback('medium');
    
    if (tariff.id === 'free') {
      alert('Вы уже используете бесплатный тариф');
      return;
    }

    if (!user?.id) {
      alert('Ошибка: не удалось определить пользователя');
      return;
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/payments/sbp/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegram_id: user.id,
          product_type: 'subscription',
          product_id: tariff.id
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create SBP subscription');
      }

      const data = await response.json();
      setSBPData({ qr_url: data.qr_url, deeplink: data.deeplink });
      setShowSBP(true);
    } catch (error) {
      console.error('Error creating SBP subscription:', error);
      alert('Не удалось создать подписку. Попробуйте позже.');
    }
  };

  return (
    <div className="energy-page">
      {/* Секция покупки энергии */}
      <div className="energy-section">
        <h2 className="energy-section__title">Купить энергию</h2>
        <p className="energy-section__subtitle">
          Разовая покупка энергии без подписки
        </p>
        <div className="packs-grid">
          {packs.map((pack, index) => (
            <div
              key={pack.id}
              className={`pack-card ${index === 1 ? 'popular' : ''}`}
            >
              <div className="pack-card__info">
                <span className="pack-card__count">{pack.energy} ⚡</span>
                {index === 1 && <span className="pack-card__badge">Популярный</span>}
              </div>
              <span className="pack-card__price">{pack.price} ₽</span>
              <div className="pack-card__buttons">
                <button 
                  className="pack-card__button"
                  onClick={() => handlePurchasePack(pack)}
                >
                  💳 Картой
                </button>
                <button 
                  className="pack-card__button pack-card__button--sbp"
                  onClick={() => handlePurchasePackSBP(pack)}
                >
                  🏦 СБП
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Секция тарифов */}
      <div className="energy-section">
        <h2 className="energy-section__title">Тарифы</h2>
        <p className="energy-section__subtitle">
          Энергия ⚡ – это валюта, которую ты тратишь на генерацию фото.<br />
          Обычный режим – 1 ⚡, PRO режим – 2 ⚡
        </p>

        <div className="tariff-cards">
          {tariffs.map((tariff) => (
            <div
              key={tariff.id}
              className={`tariff-card ${currentPlan === tariff.id ? 'tariff-card--active' : ''}`}
            >
              <div className="tariff-card__header">
                <span className="tariff-card__name">{tariff.name}</span>
                {tariff.badge && (
                  <span className={`tariff-card__badge tariff-card__badge--${tariff.badge.type}`}>
                    {tariff.badge.text}
                  </span>
                )}
              </div>
              <div className="tariff-card__price">
                <span className="tariff-card__amount">{tariff.price}</span>
                <span className="tariff-card__energy">{tariff.energy}</span>
              </div>
              <p className="tariff-card__desc">{tariff.description}</p>
              
              {tariff.id !== 'free' && (
                <div className="tariff-card__buttons">
                  <button 
                    className="tariff-card__button"
                    onClick={() => handleSelectTariff(tariff)}
                  >
                    💳 Картой
                  </button>
                  <button 
                    className="tariff-card__button tariff-card__button--sbp"
                    onClick={() => handleSelectTariffSBP(tariff)}
                  >
                    🏦 СБП
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Payment Modal */}
      <PaymentModal
        isOpen={showPaymentModal}
        onClose={() => setShowPaymentModal(false)}
        widgetParams={paymentWidgetParams}
        onSuccess={() => {
          alert('Оплата прошла успешно!');
          // TODO: Обновить баланс пользователя
        }}
        onFail={(reason) => {
          alert(`Ошибка оплаты: ${reason}`);
        }}
      />

      {/* SBP Modal */}
      {showSBP && sbpData && (
        <div className="sbp-modal-overlay" onClick={() => setShowSBP(false)}>
          <div className="sbp-modal" onClick={(e) => e.stopPropagation()}>
            <button className="sbp-modal__close" onClick={() => setShowSBP(false)}>
              ×
            </button>
            <h3>Оплата по СБП</h3>
            {sbpData.qr_url && (
              <div className="sbp-modal__qr">
                <p>Отсканируйте QR-код:</p>
                <img src={sbpData.qr_url} alt="QR код для оплаты" />
              </div>
            )}
            {sbpData.deeplink && (
              <div className="sbp-modal__link">
                <p>Или откройте в приложении банка:</p>
                <a href={sbpData.deeplink} className="sbp-modal__button">
                  Оплатить через СБП
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
