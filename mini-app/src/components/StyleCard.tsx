import { useState } from 'react';
import { Style } from '../api/client';

interface StyleCardProps {
  style: Style;
  onSelect: (style: Style) => void;
}

const categoryLabels: Record<string, string> = {
  effect: 'эффект',
  look: 'образ',
  new: 'новое',
  trending: 'тренд',
  for_her: 'для неё',
  for_him: 'для него',
};

export function StyleCard({ style, onSelect }: StyleCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleClick = () => {
    onSelect(style);
  };

  return (
    <div className="style-card" onClick={handleClick}>
      <div className="style-card__image-wrapper">
        {!imageLoaded && !imageError && (
          <div className="image-placeholder">📷</div>
        )}
        {imageError ? (
          <div className="image-placeholder">📷</div>
        ) : (
          <img
            src={style.image}
            alt={style.name}
            className="style-card__image"
            style={{ display: imageLoaded ? 'block' : 'none' }}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
          />
        )}
        
        <span className={`style-card__badge style-card__badge--${style.category}`}>
          {categoryLabels[style.category] || style.category}
        </span>
        
        <span className="style-card__name">{style.name}</span>
      </div>
      
      <button 
        className="style-card__button"
        onClick={(e) => {
          e.stopPropagation();
          handleClick();
        }}
      >
        Выбрать
      </button>
    </div>
  );
}
