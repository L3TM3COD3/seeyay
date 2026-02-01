type TabId = 'photo-ideas' | 'profile' | 'energy';

interface BottomNavigationProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export function BottomNavigation({ activeTab, onTabChange }: BottomNavigationProps) {
  return (
    <nav className="bottom-nav">
      <button
        className={`bottom-nav__item ${activeTab === 'photo-ideas' ? 'bottom-nav__item--active' : ''}`}
        onClick={() => onTabChange('photo-ideas')}
        aria-label="Фото-идеи"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
        <span>Фото-идеи</span>
      </button>

      <button
        className={`bottom-nav__item ${activeTab === 'profile' ? 'bottom-nav__item--active' : ''}`}
        onClick={() => onTabChange('profile')}
        aria-label="Профиль"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
        </svg>
        <span>Профиль</span>
      </button>

      <button
        className={`bottom-nav__item ${activeTab === 'energy' ? 'bottom-nav__item--active' : ''}`}
        onClick={() => onTabChange('energy')}
        aria-label="Энергия"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
        <span>Энергия</span>
      </button>
    </nav>
  );
}
