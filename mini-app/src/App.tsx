import { useState, useEffect, useCallback } from 'react';
import { Header, Gallery, Tabs, Profile, BottomNavigation } from './components';
// import { EnergyPage } from './pages/EnergyPage'; // Не используется, логика покупки теперь в Profile
import { Style, Category, User, fetchUser, fetchStyles } from './api/client';
import { useTelegram } from './hooks/useTelegram';

type TabId = 'photo-ideas' | 'profile';

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('photo-ideas');
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
        } else {
          // Fallback если не удалось загрузить пользователя
          console.error('Failed to fetch user data, using fallback');
          setUser({
            id: 1,
            telegram_id: tgUser.id,
            username: tgUser.username || 'user',
            plan: 'free',
            balance: 0
          });
        }
      }).catch((error) => {
        console.error('Error loading user:', error);
        // Fallback при ошибке
        setUser({
          id: 1,
          telegram_id: tgUser.id,
          username: tgUser.username || 'user',
          plan: 'free',
          balance: 0
        });
      });
    } else if (isReady) {
      // Для разработки без Telegram или когда tgUser недоступен
      console.log('Using dev/fallback user data');
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

  const handleSelectStyle = useCallback(async (style: Style) => {
    hapticFeedback('medium');
    
    // Сразу вызываем API для отправки конфигурации боту (минуя preview экран)
    const telegramId = tgUser?.id || 0;
    
    if (!telegramId) {
      console.error('No telegram user id');
      return;
    }

    const selection = {
      telegram_id: telegramId,
      style_id: style.id,
      style_name: style.name,
      mode: 'normal' as const  // По умолчанию обычный режим
    };
    
    try {
      const { submitStyleSelection } = await import('./api/client');
      const success = await submitStyleSelection(selection);
      
      if (success) {
        // Закрываем мини-апп после успешной отправки
        if (window.Telegram?.WebApp) {
          window.Telegram.WebApp.close();
        }
      } else {
        console.error('Failed to submit style selection');
        // Можно показать уведомление об ошибке
      }
    } catch (error) {
      console.error('Error submitting style selection:', error);
      // Можно показать уведомление об ошибке
    }
  }, [hapticFeedback, tgUser]);

  const handleTabChange = useCallback((tab: TabId) => {
    hapticFeedback('light');
    setActiveTab(tab);
  }, [hapticFeedback]);

  const handleEnergyClick = useCallback(() => {
    hapticFeedback('light');
    setActiveTab('profile');
  }, [hapticFeedback]);

  const handleLogoClick = useCallback(() => {
    hapticFeedback('light');
    setActiveTab('photo-ideas');
  }, [hapticFeedback]);



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

  // Основной layout с навигацией
  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <Profile 
            user={user}
            onEnergyClick={handleEnergyClick}
          />
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
