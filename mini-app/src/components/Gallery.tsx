import { Style } from '../api/client';
import { StyleCard } from './StyleCard';

interface GalleryProps {
  styles: Style[];
  onSelectStyle: (style: Style) => void;
}

export function Gallery({ styles, onSelectStyle }: GalleryProps) {
  if (styles.length === 0) {
    return (
      <div className="gallery" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
        <p style={{ color: 'var(--color-gray-500)' }}>Стили ещё не добавлены</p>
      </div>
    );
  }

  return (
    <div className="gallery">
      {styles.map((style) => (
        <StyleCard
          key={style.id}
          style={style}
          onSelect={onSelectStyle}
        />
      ))}
    </div>
  );
}
