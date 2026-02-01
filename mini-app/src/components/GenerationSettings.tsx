import { useState, useEffect } from 'react';
import { Style } from '../api/client';
import { useTelegram } from '../hooks/useTelegram';

interface GenerationSettingsProps {
  style: Style;
  userBalance: number;
  onBack: () => void;
  onSubmit: (settings: { photoCount: number; mode: 'normal' | 'pro' }) => void;
}

const photoCountOptions = [1, 3, 5, 10];

export function GenerationSettings({ style, userBalance, onBack, onSubmit }: GenerationSettingsProps) {
  const [photoCount, setPhotoCount] = useState(1);
  const [mode, setMode] = useState<'normal' | 'pro'>('normal');
  const { showBackButton, hideBackButton, hapticFeedback } = useTelegram();

  // Рассчитываем стоимость
  const cost = mode === 'pro' ? photoCount * 2 : photoCount;
  const canAfford = userBalance >= cost;

  useEffect(() => {
    showBackButton(onBack);
    return () => hideBackButton();
  }, [showBackButton, hideBackButton, onBack]);

  const handleSubmit = () => {
    if (!canAfford) {
      hapticFeedback('error');
      return;
    }
    hapticFeedback('success');
    onSubmit({ photoCount, mode });
  };

  return (
    <div className="settings-screen">
      <img 
        src={style.image} 
        alt={style.name}
        className="settings-screen__preview"
      />
      
      <h2 className="settings-screen__title settings-screen__title--left">
        {style.name}
      </h2>

      <div className="settings-section">
        <span className="settings-section__label">Количество фото</span>
        <div className="settings-options">
          {photoCountOptions.map((count) => (
            <button
              key={count}
              className={`settings-option ${photoCount === count ? 'active' : ''}`}
              onClick={() => {
                setPhotoCount(count);
                hapticFeedback('light');
              }}
            >
              {count}
            </button>
          ))}
        </div>
      </div>

      <div className="settings-section">
        <span className="settings-section__label">Режим</span>
        <div className="settings-options">
          <button
            className={`settings-option ${mode === 'normal' ? 'active' : ''}`}
            onClick={() => {
              setMode('normal');
              hapticFeedback('light');
            }}
          >
            Обычный
          </button>
          <button
            className={`settings-option settings-option--pro ${mode === 'pro' ? 'active' : ''}`}
            onClick={() => {
              setMode('pro');
              hapticFeedback('light');
            }}
          >
            ✨ PRO
          </button>
        </div>
      </div>

      <div className="settings-cost">
        <span className="settings-cost__label">Стоимость</span>
        <span className="settings-cost__value">
          {cost} ⚡
        </span>
      </div>

      {!canAfford && (
        <p style={{ color: 'var(--color-effect)', fontSize: '14px', textAlign: 'center' }}>
          Недостаточно энергии. Ваш баланс: {userBalance} ⚡
        </p>
      )}

      <button 
        className="settings-submit"
        onClick={handleSubmit}
        disabled={!canAfford}
        style={{ opacity: canAfford ? 1 : 0.5 }}
      >
        {canAfford ? 'Продолжить' : 'Пополнить баланс'}
      </button>
    </div>
  );
}
