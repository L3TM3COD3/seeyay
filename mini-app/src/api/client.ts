const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Style {
  id: string;
  name: string;
  category: string;
  image: string;
  prompt: string;
}

export interface Category {
  id: string;
  name: string;
}

export interface User {
  id: number;
  telegram_id: number;
  username: string | null;
  plan: string;
  balance: number;
}

export interface GenerationPack {
  id: string;
  energy: number;
  price: number;
  currency: string;
}

export interface Generation {
  id: string;
  image_url: string;
  style_name: string;
  prompt: string;
  created_at: string;
}

// История генераций
export async function fetchGenerationHistory(telegramId: number): Promise<Generation[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users/${telegramId}/generations`);
    if (!response.ok) throw new Error('Failed to fetch generations');
    return await response.json();
  } catch (error) {
    console.error('Error fetching generation history:', error);
    // Моковые данные для разработки
    return getMockGenerations();
  }
}

function getMockGenerations(): Generation[] {
  return [
    {
      id: 'gen_1',
      image_url: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400',
      style_name: 'Luxury-стиль',
      prompt: 'Transform this photo into a luxury fashion photoshoot style',
      created_at: '2026-01-30T12:00:00Z'
    },
    {
      id: 'gen_2',
      image_url: 'https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=400',
      style_name: 'Студийный',
      prompt: 'Transform this photo into a professional studio photoshoot',
      created_at: '2026-01-29T15:30:00Z'
    },
    {
      id: 'gen_3',
      image_url: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400',
      style_name: 'Деловой стиль',
      prompt: 'Transform this photo into a professional business portrait',
      created_at: '2026-01-28T10:00:00Z'
    },
    {
      id: 'gen_4',
      image_url: 'https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=400',
      style_name: 'Неоновый',
      prompt: 'Transform this photo with neon lighting effects',
      created_at: '2026-01-27T18:45:00Z'
    },
  ];
}

// Стили
export async function fetchStyles(category: string = 'all'): Promise<{ styles: Style[], categories: Category[] }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/styles?category=${category}`);
    if (!response.ok) throw new Error('Failed to fetch styles');
    return await response.json();
  } catch (error) {
    console.error('Error fetching styles:', error);
    // Возвращаем моковые данные для разработки
    return getMockData();
  }
}

export async function fetchStyle(styleId: string): Promise<Style | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/styles/${styleId}`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Error fetching style:', error);
    return null;
  }
}

// Пользователи
export async function fetchUser(telegramId: number): Promise<User | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users/${telegramId}`);
    if (!response.ok) {
      if (response.status === 404) {
        // Создаём нового пользователя
        return await createUser(telegramId);
      }
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching user:', error);
    // Моковые данные для разработки
    return {
      id: 1,
      telegram_id: telegramId,
      username: 'user',
      plan: 'free',
      balance: 100
    };
  }
}

export async function createUser(telegramId: number, username?: string): Promise<User | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ telegram_id: telegramId, username })
    });
    if (!response.ok) throw new Error('Failed to create user');
    return await response.json();
  } catch (error) {
    console.error('Error creating user:', error);
    return null;
  }
}

// Выбор стиля - отправка данных боту через API
export interface StyleSelection {
  telegram_id: number;
  style_id: string;
  style_name: string;
  mode: 'normal' | 'pro';
}

export async function submitStyleSelection(selection: StyleSelection): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/generate/select-style`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(selection)
    });
    if (!response.ok) throw new Error('Failed to submit style selection');
    return true;
  } catch (error) {
    console.error('Error submitting style selection:', error);
    return false;
  }
}

// Пакеты генераций
export async function fetchPacks(): Promise<GenerationPack[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/payments/packs`);
    if (!response.ok) throw new Error('Failed to fetch packs');
    const data = await response.json();
    return data.packs;
  } catch (error) {
    console.error('Error fetching packs:', error);
    return [
      { id: 'pack_10', energy: 10, price: 99, currency: 'RUB' },
      { id: 'pack_30', energy: 30, price: 249, currency: 'RUB' },
      { id: 'pack_100', energy: 100, price: 699, currency: 'RUB' },
    ];
  }
}

// Моковые данные для разработки без бэкенда
function getMockData(): { styles: Style[], categories: Category[] } {
  return {
    categories: [
      { id: 'all', name: 'Все' },
      { id: 'effect', name: 'Эффекты' },
      { id: 'look', name: 'Образ' },
    ],
    styles: [
      {
        id: 'ice_cube',
        name: 'Ледяной куб',
        category: 'effect',
        image: 'https://images.unsplash.com/photo-1483664852095-d6cc6870702d?w=400',
        prompt: 'Ice cube effect'
      },
      {
        id: 'winter_triptych',
        name: 'Зимний триптих',
        category: 'look',
        image: 'https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=400',
        prompt: 'Winter triptych collage'
      },
    ]
  };
}
