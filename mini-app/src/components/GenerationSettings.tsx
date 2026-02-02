import { useState, useEffect } from 'react';
import { Style } from '../api/client';
import { useTelegram } from '../hooks/useTelegram';

interface GenerationSettingsProps {
  style: Style;
  userBalance: number;
  onBack: () => void;
  onSubmit: (settings: { mode: 'normal' | 'pro' }) => void;
}

export function GenerationSettings({ style, userBalance, onBack, onSubmit }: GenerationSettingsProps) {
  const [mode, setMode] = useState<'normal' | 'pro'>('normal');
  const { showBackButton, hideBackButton, hapticFeedback } = useTelegram();

  // Рассчитываем стоимость генерации: normal = 1⚡, pro = 2⚡
  // Всегда генерируется только 1 фото
  const cost = mode === 'pro' ? 2 : 1;
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
    onSubmit({ mode });
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
