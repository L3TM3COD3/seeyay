import { useState, useEffect } from 'react';
import { Generation, fetchGenerationHistory } from '../api/client';
import { useTelegram } from '../hooks/useTelegram';

interface HistoryGalleryProps {
  telegramId: number;
  onBack: () => void;
  onRepeat: (prompt: string, styleName: string) => void;
}

export function HistoryGallery({ telegramId, onBack, onRepeat }: HistoryGalleryProps) {
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [loading, setLoading] = useState(true);
  const { showBackButton, hideBackButton, hapticFeedback } = useTelegram();

  useEffect(() => {
    showBackButton(onBack);
    return () => hideBackButton();
  }, [showBackButton, hideBackButton, onBack]);

  useEffect(() => {
    setLoading(true);
    fetchGenerationHistory(telegramId)
      .then(setGenerations)
      .finally(() => setLoading(false));
  }, [telegramId]);

  const handleRepeat = (generation: Generation) => {
    hapticFeedback('medium');
    onRepeat(generation.prompt, generation.style_name);
  };

  if (loading) {
    return (
      <div className="history-screen">
        <h2 className="history-screen__title">Мои фото</h2>
        <div className="loading">
          <div className="loading-spinner" />
        </div>
      </div>
    );
  }

  if (generations.length === 0) {
    return (
      <div className="history-screen">
        <h2 className="history-screen__title">Мои фото</h2>
        <div className="history-empty">
          <p>У вас пока нет сгенерированных фото</p>
          <p className="history-empty__hint">Выберите стиль и создайте своё первое фото!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="history-screen">
      <h2 className="history-screen__title">Мои фото</h2>
      <div className="history-gallery">
        {generations.map((generation) => (
          <div key={generation.id} className="history-card">
            <div className="history-card__image-wrapper">
              <img
                src={generation.image_url}
                alt={generation.style_name}
                className="history-card__image"
              />
            </div>
            <div className="history-card__content">
              <span className="history-card__name">{generation.style_name}</span>
              <button
                className="history-card__button"
                onClick={() => handleRepeat(generation)}
              >
                Повторить
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
