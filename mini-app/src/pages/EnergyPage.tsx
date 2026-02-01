import { useEffect, useState } from 'react';
import { GenerationPack, fetchPacks } from '../api/client';
import { useTelegram } from '../hooks/useTelegram';

interface EnergyPageProps {
  currentPlan: string;
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

// Начальные данные для мгновенного отображения
const defaultPacks: GenerationPack[] = [
  { id: 'pack_10', generations: 10, price: 99, currency: 'RUB' },
  { id: 'pack_30', generations: 30, price: 249, currency: 'RUB' },
  { id: 'pack_100', generations: 100, price: 699, currency: 'RUB' },
];

export function EnergyPage({ currentPlan }: EnergyPageProps) {
  const [packs, setPacks] = useState<GenerationPack[]>(defaultPacks);
  const { hapticFeedback } = useTelegram();

  useEffect(() => {
    fetchPacks().then(setPacks);
  }, []);

  const handlePurchase = (pack: GenerationPack) => {
    hapticFeedback('medium');
    // TODO: Интеграция с платежной системой
    alert(`Покупка ${pack.generations} ⚡ за ${pack.price} ₽\n\nИнтеграция с платежной системой в разработке.`);
  };

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
              onClick={() => handlePurchase(pack)}
            >
              <div className="pack-card__info">
                <span className="pack-card__count">{pack.generations} ⚡</span>
                {index === 1 && <span className="pack-card__badge">Популярный</span>}
              </div>
              <span className="pack-card__price">{pack.price} ₽</span>
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
    </div>
  );
}
