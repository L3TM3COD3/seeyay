import { useEffect } from 'react';
import { useTelegram } from '../hooks/useTelegram';

interface TariffScreenProps {
  currentPlan: string;
  onBack: () => void;
}

interface Tariff {
  id: string;
  name: string;
  price: string;
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
    price: 'Бесплатно',
    energy: '1 ⚡ / день',
    description: '1 фото в обычном режиме генерации, кредиты обновляются каждый день в 00:00 по МСК',
  },
  {
    id: 'basic',
    name: 'Basic',
    price: '499 ₽',
    energy: '30 ⚡ / месяц',
    description: '30 фото в обычном режиме генерации и 15 фото в PRO режиме генерации',
    badge: {
      text: 'Популярный',
      type: 'popular',
    },
  },
  {
    id: 'pro',
    name: 'PRO',
    price: '1299 ₽',
    energy: '100 ⚡ / месяц',
    description: '100 фото в обычном режиме генерации и 50 фото в PRO режиме генерации',
    badge: {
      text: 'Выгодный',
      type: 'best',
    },
  },
];

export function TariffScreen({ currentPlan, onBack }: TariffScreenProps) {
  const { showBackButton, hideBackButton, hapticFeedback } = useTelegram();

  useEffect(() => {
    showBackButton(onBack);
    return () => hideBackButton();
  }, [showBackButton, hideBackButton, onBack]);

  const handleSelectTariff = (tariff: Tariff) => {
    hapticFeedback('medium');
    if (tariff.id === 'free') {
      alert('Вы уже используете бесплатный тариф');
      return;
    }
    // TODO: Интеграция с платежной системой
    alert(`Покупка тарифа ${tariff.name} за ${tariff.price}\n\nИнтеграция с платежной системой в разработке.`);
  };

  return (
    <div className="tariff-screen">
      <h2 className="tariff-screen__title">Тарифы</h2>
      <p className="tariff-screen__subtitle">
        Энергия ⚡ – это валюта, которую ты тратишь на генерацию фото.<br />
        Обычный режим – 1 ⚡, PRO режим – 2 ⚡
      </p>

      <div className="tariff-cards">
        {tariffs.map((tariff) => (
          <div
            key={tariff.id}
            className={`tariff-card ${currentPlan === tariff.id ? 'tariff-card--active' : ''}`}
            onClick={() => handleSelectTariff(tariff)}
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
          </div>
        ))}
      </div>
    </div>
  );
}
