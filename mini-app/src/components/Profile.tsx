import { useEffect, useState } from 'react';
import { User, Generation, fetchGenerationHistory } from '../api/client';
import { useTelegram } from '../hooks/useTelegram';

interface ProfileProps {
  user: User;
  onEnergyClick: () => void;
  onRepeat: (prompt: string, styleName: string) => void;
}

const planNames: Record<string, string> = {
  free: 'Free',
  basic: 'Basic',
  pro: 'Pro',
};

export function Profile({ user, onEnergyClick, onRepeat }: ProfileProps) {
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [loading, setLoading] = useState(true);
  const { hapticFeedback } = useTelegram();

  useEffect(() => {
    setLoading(true);
    fetchGenerationHistory(user.telegram_id)
      .then(setGenerations)
      .finally(() => setLoading(false));
  }, [user.telegram_id]);

  const handleRepeat = (generation: Generation) => {
    hapticFeedback('medium');
    onRepeat(generation.prompt, generation.style_name);
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
        <h2 className="profile-name">
          {user.username || `Пользователь ${user.telegram_id}`}
        </h2>
        <p className="profile-id">ID: {user.telegram_id}</p>
      </div>

      <div 
        className="profile-tariff-block"
        onClick={() => {
          hapticFeedback('light');
          onEnergyClick();
        }}
      >
        <div className="profile-tariff-block__left">
          <span className="profile-tariff-block__label">Тариф</span>
          <span className="profile-tariff-block__value">{planNames[user.plan]}</span>
        </div>
        <div className="profile-tariff-block__right">
          <span className="profile-tariff-block__energy">{user.balance} ⚡</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="profile-tariff-block__arrow">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>
      </div>

      <div className="profile-history">
        <h3 className="profile-history__title">Мои фото</h3>
        
        {loading ? (
          <div className="loading">
            <div className="loading-spinner" />
          </div>
        ) : generations.length === 0 ? (
          <div className="history-empty">
            <p>У вас пока нет сгенерированных фото</p>
            <p className="history-empty__hint">Выберите стиль и создайте своё первое фото!</p>
          </div>
        ) : (
          <div className="gallery">
            {generations.map((generation) => (
              <div key={generation.id} className="style-card" onClick={() => handleRepeat(generation)}>
                <div className="style-card__image-wrapper">
                  <img
                    src={generation.image_url}
                    alt={generation.style_name}
                    className="style-card__image"
                  />
                  <span className="style-card__name">{generation.style_name}</span>
                </div>
                <button
                  className="style-card__button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRepeat(generation);
                  }}
                >
                  Повторить
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
