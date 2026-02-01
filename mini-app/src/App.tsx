import { useState, useEffect, useCallback } from 'react';
import { Header, GenerationSettings, Gallery, Tabs, Profile, BottomNavigation } from './components';
import { EnergyPage } from './pages/EnergyPage';
import { Style, Category, User, fetchUser, fetchStyles } from './api/client';
import { useTelegram } from './hooks/useTelegram';

type TabId = 'photo-ideas' | 'profile' | 'energy';
type Screen = TabId | 'settings';

function App() {
  const [screen, setScreen] = useState<Screen>('photo-ideas');
  const [activeTab, setActiveTab] = useState<TabId>('photo-ideas');
  const [selectedStyle, setSelectedStyle] = useState<Style | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [styles, setStyles] = useState<Style[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const { user: tgUser, isReady, hapticFeedback } = useTelegram();

  // Загружаем данные пользователя
  useEffect(() => {
    if (isReady && tgUser) {
      fetchUser(tgUser.id).then((userData) => {
        if (userData) {
          setUser(userData);
        }
      });
    } else if (isReady) {
      // Для разработки без Telegram
      setUser({
        id: 1,
        telegram_id: 123456789,
        username: 'test_user',
        plan: 'free',
        balance: 100
      });
    }
  }, [isReady, tgUser]);

  // Загружаем стили
  useEffect(() => {
    loadStyles();
  }, []);

  const loadStyles = async () => {
    setLoading(true);
    try {
      const data = await fetchStyles();
      setStyles(data.styles);
      setCategories(data.categories);
    } catch (error) {
      console.error('Failed to load styles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (category: string) => {
    setActiveCategory(category);
  };

  const filteredStyles = activeCategory === 'all' 
    ? styles 
    : styles.filter(s => s.category === activeCategory);

  const handleSelectStyle = useCallback((style: Style) => {
    hapticFeedback('medium');
    setSelectedStyle(style);
    setScreen('settings');
  }, [hapticFeedback]);

  const handleTabChange = useCallback((tab: TabId) => {
    hapticFeedback('light');
    setActiveTab(tab);
    setScreen(tab);
    setSelectedStyle(null);
  }, [hapticFeedback]);

  const handleEnergyClick = useCallback(() => {
    hapticFeedback('light');
    setActiveTab('energy');
    setScreen('energy');
  }, [hapticFeedback]);

  const handleLogoClick = useCallback(() => {
    hapticFeedback('light');
    setActiveTab('photo-ideas');
    setScreen('photo-ideas');
    setSelectedStyle(null);
  }, [hapticFeedback]);

  const handleBack = useCallback(() => {
    hapticFeedback('light');
    setScreen(activeTab);
    setSelectedStyle(null);
  }, [hapticFeedback, activeTab]);

  const handleRepeatGeneration = useCallback((prompt: string, styleName: string) => {
    // Находим стиль по имени или создаём временный объект
    const tempStyle: Style = {
      id: 'repeat',
      name: styleName,
      category: 'effect',
      image: '',
      prompt: prompt
    };
    setSelectedStyle(tempStyle);
    setScreen('settings');
  }, []);

  const handleSubmitGeneration = useCallback(async (settings: { photoCount: number; mode: 'normal' | 'pro' }) => {
    if (!selectedStyle) {
      console.error('No style selected');
      return;
    }

    // Используем API-подход вместо sendData() для надёжности
    // sendData() не всегда работает в зависимости от способа открытия мини-аппа
    const telegramId = tgUser?.id || 0;
    
    if (!telegramId) {
      console.error('No telegram user id');
      return;
    }

    const selection = {
      telegram_id: telegramId,
      style_id: selectedStyle.id,
      style_name: selectedStyle.name,
      photo_count: settings.photoCount,
      mode: settings.mode
    };
    
    try {
      const { submitStyleSelection } = await import('./api/client');
      const success = await submitStyleSelection(selection);
      
      if (success) {
        // Закрываем мини-апп
        if (window.Telegram?.WebApp) {
          window.Telegram.WebApp.close();
        }
      } else {
        console.error('Failed to submit style selection');
      }
    } catch (error) {
      console.error('Error submitting style selection:', error);
    }
  }, [selectedStyle, tgUser]);

  // Показываем загрузку пока нет данных пользователя
  if (!user) {
    return (
      <div className="app" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div className="loading">
          <div className="loading-spinner" />
        </div>
      </div>
    );
  }

  // Экран настроек генерации
  if (screen === 'settings' && selectedStyle) {
    return (
      <div className="app">
        <Header 
          balance={user.balance}
          onEnergyClick={handleEnergyClick}
          onLogoClick={handleLogoClick}
        />
        <main className="app-content">
          <GenerationSettings
            style={selectedStyle}
            userBalance={user.balance}
            onBack={handleBack}
            onSubmit={handleSubmitGeneration}
          />
        </main>
        <BottomNavigation 
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      </div>
    );
  }

  // Основной layout с навигацией
  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <Profile 
            user={user}
            onEnergyClick={handleEnergyClick}
            onRepeat={handleRepeatGeneration}
          />
        );

      case 'energy':
        return (
          <EnergyPage currentPlan={user.plan} />
        );

      case 'photo-ideas':
      default:
        return (
          <>
            <Tabs 
              categories={categories}
              activeCategory={activeCategory}
              onCategoryChange={handleCategoryChange}
            />
            {loading ? (
              <div className="loading">
                <div className="loading-spinner" />
              </div>
            ) : (
              <Gallery 
                styles={filteredStyles}
                onSelectStyle={handleSelectStyle}
              />
            )}
          </>
        );
    }
  };

  return (
    <div className="app">
      <Header 
        balance={user.balance}
        onEnergyClick={handleEnergyClick}
        onLogoClick={handleLogoClick}
      />
      <main className="app-content">
        {renderContent()}
      </main>
      <BottomNavigation 
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />
    </div>
  );
}

export default App;
