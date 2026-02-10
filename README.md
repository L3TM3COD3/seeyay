# СИЯЙ AI - Telegram бот для нейрофотосессий

Telegram бот с Mini App для создания AI-фотосессий в различных стилях с интегрированной системой платежей.

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Google Cloud (europe-west4)                      │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Cloud Run   │  │  Cloud Run   │  │  Cloud Run   │              │
│  │    Bot       │  │    API       │  │  Mini App    │              │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘              │
│         │                 │                                          │
│         │    ┌────────────┴────────────┐                            │
│         │    │                         │                            │
│  ┌──────▼────▼──┐  ┌──────────────┐  ┌▼─────────────┐             │
│  │   Firestore  │  │Secret Manager│  │  Vertex AI   │             │
│  │   Database   │  │   (secrets)  │  │ (Gemini API) │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                       │
│  ┌──────────────────┐  ┌────────────────────┐                      │
│  │ Cloud Scheduler  │  │  CloudPayments API │ (external)           │
│  │  (Cron Jobs)     │  │    + СБП           │                      │
│  └──────────────────┘  └────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Возможности

### Основные функции
- 🎨 Галерея стилей фотосессий (Ледяной куб, Зимний триптих)
- 👤 Баланс пользователя с энергией (⚡)
- 🖼️ Генерация фото в стиле (Обычный = 1⚡, PRO = 6⚡)
- 💡 Автоматическое списание и возврат энергии
- 🎯 Умная цепочка сообщений с онбордингом (14 сообщений)

### 🚧 В разработке
- **📥 Скачивание в высоком качестве**: Функция временно скрыта. Для реализации требуется подключение Google Cloud Storage (GCS) для хранения оригиналов изображений. Текущая логика в коде (`handle_download` в `bot/handlers/photo.py`) готова, необходимо добавить:
  - Сохранение `result_bytes` из Vertex AI в GCS bucket
  - Загрузка оригинала из GCS при нажатии кнопки "Скачать файл"
  - Настройка TTL (24 часа) для автоудаления старых файлов

### Платежная система
- 💳 **Покупка пакетов энергии** (единоразово)
  - 10⚡ = 249₽ (10 фото)
  - 50⚡ = 790₽ (50 фото) — популярно
  - 120⚡ = 1290₽ (120 фото) — выгодно
  - 300⚡ = 2490₽ (300 фото)
  - 🔥 **Стартер-пак**: 100⚡ = 990₽ (для новых пользователей)
  - 🎁 **Пробный пак**: 8⚡ = 169₽ (downsell)
- ⚡ **Бесплатная энергия**: 3⚡ на старте, затем 1⚡ в день при нулевом балансе
- 🏦 **Оплата через СБП** (QR-код + deeplink)
- 📱 **Онлайн-чеки** (54-ФЗ) через CloudKassir

## 📁 Структура проекта

```
Seeyay.ai/
├── bot/                       # Telegram бот (aiogram)
│   ├── Dockerfile         
│   ├── handlers/              # Обработчики команд
│   │   ├── start.py          # /start, /menu команды
│   │   ├── template_selection.py  # Выбор шаблонов, переключение режимов
│   │   ├── photo.py          # Обработка фото + генерация
│   │   ├── energy.py         # Покупка пакетов, навигация
│   │   └── webapp.py         # Web App данные
│   ├── services/              # Сервисы
│   │   └── vertex_ai.py      # Генерация через Vertex AI
│   ├── messages.py            # 14 текстов сообщений (m1-m14)
│   ├── keyboards.py           # Inline клавиатуры
│   ├── firestore.py           # Firestore операции
│   └── main.py            
│
├── backend/                   # FastAPI сервер
│   ├── Dockerfile         
│   ├── routers/               # API endpoints
│   │   ├── styles.py         # Стили
│   │   ├── users.py          # Пользователи
│   │   ├── payments.py       # Платежи (пакеты + подписки)
│   │   ├── webhooks.py       # CloudPayments webhooks
│   │   ├── cron.py           # Cron endpoints
│   │   └── generate.py       # Генерация
│   ├── services/              # Бизнес-логика
│   │   ├── cloudpayments.py  # CloudPayments клиент
│   │   ├── subscription.py   # Управление подписками
│   │   └── notifications.py  # Уведомления в Telegram
│   ├── firestore.py           # Работа с Firestore
│   ├── secrets.py             # Secret Manager
│   └── main.py            
│
├── mini-app/                  # React Mini App
│   ├── Dockerfile         
│   ├── src/
│   │   ├── components/       # React компоненты
│   │   │   ├── Gallery.tsx
│   │   │   ├── Profile.tsx   # Переименован в "Баланс"
│   │   │   ├── PaymentModal.tsx
│   │   │   └── ...
│   │   ├── pages/
│   │   │   └── EnergyPage.tsx
│   │   └── api/
│   │       └── client.ts
│   └── ...
│
├── docs/                      # Документация
│   ├── messages-part1.md      # Цепочка сообщений (m1-m5)
│   ├── messages-part2.md      # Цепочка сообщений (m6-m9)
│   └── messages-part3.md      # Цепочка сообщений (m10-m14)
│
├── cloudbuild.yaml            # CI/CD production
├── cloudbuild-dev.yaml        # CI/CD development
└── TROUBLESHOOTING.md         # Решение проблем
```

## ⚙️ Настройка Google Cloud

### 1. Создание проекта

```bash
# Создайте новый проект или выберите существующий
gcloud projects create seeyay-ai --name="СИЯЙ AI"
gcloud config set project seeyay-ai
```

### 2. Включение API

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    cloudscheduler.googleapis.com
```

### 3. Создание секретов

```bash
# Telegram Bot Token (получите у @BotFather)
echo -n "YOUR_BOT_TOKEN" | gcloud secrets create telegram-bot-token \
    --data-file=- --replication-policy="automatic"

# CloudPayments Public ID
echo -n "YOUR_PUBLIC_ID" | gcloud secrets create cloudpayments-public-id \
    --data-file=- --replication-policy="automatic"

# CloudPayments API Secret
echo -n "YOUR_API_SECRET" | gcloud secrets create cloudpayments-api-secret \
    --data-file=- --replication-policy="automatic"

# Cron Auth Token (для безопасности cron endpoints)
openssl rand -base64 32 | gcloud secrets create cron-auth-token \
    --data-file=- --replication-policy="automatic"
```

### 4. Настройка Firestore

```bash
# Создайте базу данных Firestore в режиме Native
gcloud firestore databases create --location=europe-west4
```

## 🚀 Деплой

### Production деплой

⚠️ **ВАЖНО:** Перед деплоем на production обязательно выполните Pre-Production Checklist ниже!

```bash
# Деплой на production (seeyay-ai)
gcloud builds submit . --config=cloudbuild.yaml --project=seeyay-ai
```

#### ⚠️ Pre-Production Checklist

Перед деплоем на production удалите весь dev-only код. Все dev-функции помечены комментариями `# DEV ONLY - REMOVE BEFORE PROD`.

##### Шаг 1: Удалите файлы и папки

```bash
# Удалите файл с dev-командами
rm bot/handlers/dev_commands.py

# Удалите папку со скриптами
rm -rf scripts/
```

##### Шаг 2: Очистите `bot/handlers/__init__.py`

**Было:**
```python
from .start import router as start_router
from .photo import router as photo_router
from .template_selection import router as template_selection_router
from .energy import router as energy_router
from .dev_commands import router as dev_commands_router  # DEV ONLY - REMOVE BEFORE PROD

__all__ = [
    "start_router",
    "template_selection_router",
    "energy_router",
    "photo_router",
    "dev_commands_router"  # DEV ONLY - REMOVE BEFORE PROD
]
```

**Стало:**
```python
from .start import router as start_router
from .photo import router as photo_router
from .template_selection import router as template_selection_router
from .energy import router as energy_router

__all__ = [
    "start_router",
    "template_selection_router",
    "energy_router",
    "photo_router"
]
```

##### Шаг 3: Очистите `bot/main.py`

**Найдите блок импортов (примерно строка 63-70):**

**Было:**
```python
from bot.handlers import (
    start_router,
    template_selection_router,
    energy_router,
    photo_router,
    dev_commands_router  # DEV ONLY - REMOVE BEFORE PROD
)
```

**Стало:**
```python
from bot.handlers import (
    start_router,
    template_selection_router,
    energy_router,
    photo_router
)
```

**Найдите регистрацию роутеров (примерно строка 93-98):**

**Было:**
```python
dp.include_router(start_router)
dp.include_router(template_selection_router)
dp.include_router(energy_router)
dp.include_router(photo_router)
dp.include_router(dev_commands_router)  # DEV ONLY - REMOVE BEFORE PROD
```

**Стало:**
```python
dp.include_router(start_router)
dp.include_router(template_selection_router)
dp.include_router(energy_router)
dp.include_router(photo_router)
```

##### Шаг 4: Проверка удаления

Выполните эти команды — они **НЕ ДОЛЖНЫ** ничего находить:

```bash
# Проверка 1: Поиск файла dev_commands
ls bot/handlers/dev_commands.py 2>/dev/null && echo "❌ ОШИБКА: Файл dev_commands.py еще существует!" || echo "✅ OK"

# Проверка 2: Поиск папки scripts
ls -d scripts/ 2>/dev/null && echo "❌ ОШИБКА: Папка scripts/ еще существует!" || echo "✅ OK"

# Проверка 3: Поиск импортов dev_commands
grep -r "dev_commands" bot/ && echo "❌ ОШИБКА: Найдены импорты dev_commands!" || echo "✅ OK"

# Проверка 4: Поиск dev-команд в коде
grep -r "_reset\|_addbalance" bot/handlers/ && echo "❌ ОШИБКА: Найдены dev-команды!" || echo "✅ OK"

# Проверка 5: Поиск маркеров DEV ONLY
grep -r "DEV ONLY" bot/ backend/ && echo "❌ ОШИБКА: Найдены маркеры DEV ONLY!" || echo "✅ OK"

# Итоговая проверка (все в одном)
echo "=== ФИНАЛЬНАЯ ПРОВЕРКА ==="
! ls bot/handlers/dev_commands.py 2>/dev/null && \
! ls -d scripts/ 2>/dev/null && \
! grep -r "dev_commands" bot/ 2>/dev/null && \
! grep -r "_reset\|_addbalance" bot/handlers/ 2>/dev/null && \
! grep -r "DEV ONLY" bot/ backend/ 2>/dev/null && \
echo "✅ ВСЁ ЧИСТО! Можно деплоить на production." || \
echo "❌ НАЙДЕНЫ ОСТАТКИ DEV-КОДА! Проверьте вывод выше."
```

##### Что должно быть удалено (полный список):

| Файл/Папка | Действие |
|------------|----------|
| `bot/handlers/dev_commands.py` | **Удалить файл** |
| `scripts/` | **Удалить папку** целиком |
| `bot/handlers/__init__.py` | Удалить 2 строки с `dev_commands_router` |
| `bot/main.py` | Удалить 2 строки с `dev_commands_router` |

**После удаления в коде НЕ ДОЛЖНО быть:**
- ❌ Строк с `dev_commands`
- ❌ Команд `/_reset` или `/_addbalance`
- ❌ Комментариев `# DEV ONLY`
- ❌ Файла `bot/handlers/dev_commands.py`
- ❌ Папки `scripts/`

### Development деплой

Для разработки используется отдельный GCP проект `seeyay-ai-dev` с полной изоляцией:
- Отдельная Firestore база данных
- Отдельный Telegram бот (@siay_ai_dev_bot)
- Отдельные Cloud Run сервисы
- Отдельные секреты в Secret Manager

```bash
# Деплой на dev (seeyay-ai-dev)
gcloud builds submit . --config=cloudbuild-dev.yaml --project=seeyay-ai-dev
```

**Важно:** `cloudbuild-dev.yaml` автоматически передаёт `--build-arg VITE_API_URL` 
для Mini App, чтобы она обращалась к dev API, а не к production.

### Альтернатива: ручной деплой

```bash
# Production
gcloud builds submit . --config=cloudbuild.yaml --project=seeyay-ai

# Development  
gcloud builds submit . --config=cloudbuild-dev.yaml --project=seeyay-ai-dev
```

## 🧪 Development Environment (Dev)

Проект поддерживает **полную изоляцию** между production и development окружениями.

### Два GCP проекта

| Параметр | Production | Development |
|----------|-----------|-------------|
| **GCP Project** | `seeyay-ai` | `seeyay-ai-dev` |
| **Project Number** | `445810320877` | `269162169877` |
| **Telegram Bot** | @siay_ai_bot | @siay_ai_dev_bot |
| **Firestore** | Отдельная БД | Отдельная БД |
| **Cloud Build** | `cloudbuild.yaml` | `cloudbuild-dev.yaml` |

### Настройка dev окружения

1. **Создайте dev проект** (если ещё не создан):
```bash
gcloud projects create seeyay-ai-dev --name="СИЯЙ AI Dev"
```

2. **Включите API**:
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    --project=seeyay-ai-dev
```

3. **Создайте dev бота** у @BotFather и сохраните токен

4. **Создайте секреты**:
```bash
echo -n "DEV_BOT_TOKEN" | gcloud secrets create telegram-bot-token \
    --data-file=- --replication-policy="automatic" --project=seeyay-ai-dev
```

5. **Выдайте права Cloud Run**:
```bash
PROJECT_NUMBER=269162169877

# Firestore
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/datastore.user"

# Secret Manager  
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Vertex AI
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### Workflow разработки

```bash
# 1. Работаем в dev ветке
git checkout dev

# 2. Деплоим на dev окружение
gcloud builds submit . --config=cloudbuild-dev.yaml --project=seeyay-ai-dev

# 3. Тестируем в dev боте (@siay_ai_dev_bot)

# 4. Когда всё ОК — мержим в main и деплоим на prod
git checkout main
git merge dev
gcloud builds submit . --config=cloudbuild.yaml --project=seeyay-ai
```

### Безопасность кода

Код **универсальный** и работает в обоих окружениях:
- URL'ы берутся из environment variables
- Dockerfile Mini App имеет **production URL по умолчанию**
- `cloudbuild-dev.yaml` переопределяет URL через `--build-arg`
- Деплой на неправильный проект **невозможен** — проект указывается явно

## 💳 Настройка CloudPayments

Подробные инструкции в **[CLOUDPAYMENTS_SETUP.md](CLOUDPAYMENTS_SETUP.md)**

### Краткий чеклист:
1. ✅ Зарегистрироваться на [CloudPayments](https://cloudpayments.ru)
2. ✅ Получить Public ID и API Secret
3. ✅ Создать секреты в Secret Manager
4. ✅ Настроить webhook'и в личном кабинете CloudPayments
5. ✅ Подключить онлайн-кассу CloudKassir
6. ✅ Настроить Cloud Scheduler jobs

## 🗄️ API Endpoints

### Основные

| Метод | Путь | Описание |
|-------|------|----------|
| GET | /api/health | Health check |
| GET | /api/styles | Список стилей |
| GET | /api/styles/{id} | Информация о стиле |
| GET | /api/users/{telegram_id} | Профиль пользователя |
| POST | /api/users | Создать пользователя |
| PATCH | /api/users/{id}/balance | Обновить баланс |

### Платежи

| Метод | Путь | Описание |
|-------|------|----------|
| GET | /api/payments/packs | Пакеты энергии |
| GET | /api/payments/plans | Тарифные планы |
| POST | /api/payments/create-pack-payment | Инициация оплаты пакета |
| POST | /api/payments/create-subscription | Инициация подписки |
| POST | /api/payments/sbp/create | Создание СБП платежа |
| POST | /api/payments/cancel-subscription | Отмена подписки |
| POST | /api/payments/resume-subscription | Возобновление подписки |

### Webhooks (CloudPayments)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | /api/webhooks/cloudpayments/check | Проверка платежа |
| POST | /api/webhooks/cloudpayments/pay | Успешная оплата |
| POST | /api/webhooks/cloudpayments/fail | Неудачная оплата |
| POST | /api/webhooks/cloudpayments/recurrent | Рекуррентный платёж |
| POST | /api/webhooks/cloudpayments/refund | Возврат |

### Cron Jobs

| Метод | Путь | Описание | Расписание |
|-------|------|----------|------------|
| POST | /api/cron/daily-energy | Начисление 1⚡ free пользователям | 00:00 МСК |
| POST | /api/cron/subscription-retry | Retry неудачных платежей | Каждые 30 мин |
| POST | /api/cron/subscription-status | Обновление статусов подписок | Каждый час |

## 🎨 Стили

Стили определены в `backend/styles_data.py` и `bot/styles_data.py`. Каждый стиль содержит:
- `id` - уникальный идентификатор
- `name` - название на русском
- `category` - категория (effect, look, new, trending, for_her, for_him)
- `image` - путь к превью
- `prompt` - промпт для Vertex AI

## 💎 Тарифы и цены

### Пакеты энергии (единоразово)

| Пакет | Цена | Энергия | Примечание |
|-------|------|---------|------------|
| Маленький | 249₽ | 10⚡ | 10 фото |
| Средний | 790₽ | 50⚡ | Популярно |
| Большой | 1290₽ | 120⚡ | Выгодно |
| Премиум | 2490₽ | 300⚡ | 300 фото |
| **🔥 Стартер-пак** | **990₽** | **100⚡** | **Для новых (70+30 бонус)** |
| **🎁 Пробный** | **169₽** | **8⚡** | **Downsell** |

### Стоимость генерации

- **Обычный режим**: 1⚡ за 1 фото
- **PRO режим**: 6⚡ за 1 фото

### Бесплатная энергия

- **На старте**: 3⚡ (выдаётся один раз)
- **Ежедневно**: 1⚡ в 00:00 МСК (если баланс = 0)

## 🔄 Логика подписок

> **📝 Примечание:** Подписочная логика временно скрыта из интерфейса пользователей. Основной способ монетизации — покупка пакетов энергии. Код подписок сохранён для будущего использования.

### Статусы подписки

| Статус | Описание |
|--------|----------|
| **active** | Оплачено, доступ есть |
| **grace** | Платёж не прошёл, идёт грейс (72 часа), доступ сохраняется |
| **suspended** | Переведён на free plan, но ещё можем вернуть |
| **canceled** | Отменена пользователем, переведён на free plan |
| **expired** | Закончился период и не восстановили, переведён на free plan |

### Retry логика

При неудачном автосписании:
1. **D0** (сразу): переход в GRACE, отправка уведомления
2. **Retry #1**: через 12 часов
3. **Retry #2**: через 24 часа после Retry #1
4. **Retry #3**: через 48 часов после Retry #2
5. **D3-D4**: если всё ещё fail → SUSPENDED (free plan)
6. **Через 7 дней**: SUSPENDED → EXPIRED (предложение скидки 25%)

## 🔧 Cloud Run Services

| Сервис | Описание | Memory | Min/Max | Секреты |
|--------|----------|--------|---------|---------|
| seeyay-bot | Telegram бот | 512Mi | 1/3 | telegram-bot-token |
| seeyay-api | Backend API | 1Gi | 0/10 | cloudpayments-* |
| seeyay-miniapp | React Mini App | 256Mi | 0/5 | - |

## 📝 После деплоя

1. Получите URL Mini App из Cloud Run
2. Настройте Menu Button в @BotFather:
   - `/mybots` → Ваш бот → Bot Settings → Menu Button
   - Укажите URL Mini App
3. Настройте webhook'и в CloudPayments (см. CLOUDPAYMENTS_SETUP.md)
4. Создайте Cloud Scheduler jobs для cron задач
5. Настройте домен seeyay.app для webhook'ов

## 🗄️ Структура данных Firestore

### Коллекция: `users`

```javascript
{
  "telegram_id": 123456789,
  "username": "user",
  "plan": "free",              // free | basic | pro
  "balance": 30,               // текущая энергия
  "successful_generations": 0, // счётчик успешных генераций
  "is_new_user": true,         // никогда не покупал пакеты
  "starter_pack_purchased": false,
  "m9_shown": false,           // показывали ли стартер-пак
  "m7_1_sent": false,          // отправлено ли сообщение после 1-й генерации
  "m7_2_sent": false,          // отправлено ли сообщение после 2-й генерации
  "m7_3_sent": false,          // отправлено ли сообщение после 3-й генерации
  "subscription": {
    "status": "active",        // active | grace | suspended | canceled | expired
    "plan": "basic",
    "token": "recurrent_token",
    "started_at": Timestamp,
    "next_billing_at": Timestamp,
    "grace_ends_at": Timestamp | null,
    "retry_count": 0,
    "last_retry_at": Timestamp | null,
    "canceled_at": Timestamp | null,
    "discount_percent": 0
  },
  "daily_energy_given_at": Timestamp,
  "created_at": Timestamp
}
```

### Коллекция: `payments`

```javascript
{
  "id": "auto",
  "user_id": "telegram_id",
  "type": "one_time | subscription | renewal",
  "product": "pack_10 | pack_50 | pack_120 | pack_300 | pack_starter | pack_downsell | basic | pro",
  "amount": 249,
  "currency": "RUB",
  "status": "pending | completed | failed | refunded",
  "cloudpayments_transaction_id": "123456",
  "payment_method": "card | sbp",
  "receipt_url": "url",
  "error_message": null,
  "created_at": Timestamp,
  "completed_at": Timestamp
}
```

### Коллекция: `generations`

```javascript
{
  "id": "auto",
  "user_id": "telegram_id",
  "style_id": "luxury",
  "mode": "normal | pro",
  "status": "pending | completed | failed",
  "created_at": Timestamp
}
```

## 🔒 Безопасность

- ✅ Секреты хранятся в Secret Manager
- ✅ IAM роли для сервисных аккаунтов
- ✅ HTTPS для всех сервисов (автоматически в Cloud Run)
- ✅ Проверка HMAC подписи webhook'ов CloudPayments
- ✅ Авторизация для cron endpoints
- ✅ Атомарные транзакции в Firestore для списания энергии
- ✅ Firestore Security Rules (настройте при необходимости)

## 📱 Уведомления в Telegram

Бот отправляет уведомления о:
- ✅ Успешной оплате пакета/подписки
- ✅ Продлении подписки
- ⚠️ Неудачном платеже (GRACE)
- 😔 Переходе в SUSPENDED
- 🎁 Предложении скидки (EXPIRED/CANCELED)
- ⚡ Недостаточной энергии
- 💰 Возврате средств

## 🧪 Тестирование

### Тестовые карты CloudPayments

- **Успешная оплата**: `4242 4242 4242 4242`
- **Отклоненная оплата**: `4000 0000 0000 0002`
- **3-D Secure**: `4000 0000 0000 3220`

CVV: любой (123), Срок: любая будущая дата

### Проверка логов

```bash
# Логи Cloud Run API
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-api" \
    --limit=50

# Логи Bot
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-bot" \
    --limit=50

# Логи Cloud Scheduler
gcloud logging read "resource.type=cloud_scheduler_job" \
    --limit=50
```

## 🐛 Troubleshooting

Для подробного руководства по решению проблем см. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

### Webhook'и не приходят
- Проверьте URL в настройках CloudPayments
- Убедитесь, что домен доступен по HTTPS
- Проверьте логи Cloud Run API

### Ошибка проверки подписи
- Убедитесь, что API Secret правильно сохранен в Secret Manager
- Проверьте кодировку (UTF-8)

### Cron jobs не выполняются
- Проверьте расписание: `gcloud scheduler jobs list --location=europe-west4`
- Убедитесь, что Cloud Run API доступен
- Проверьте авторизацию

### Проблемы при деплое dev окружения
- См. детальный checklist в [TROUBLESHOOTING.md](TROUBLESHOOTING.md#-checklist-для-настройки-нового-dev-окружения)

## 📚 Полезные ссылки

### Документация проекта
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Решение типичных проблем
- [CLOUDPAYMENTS_SETUP.md](CLOUDPAYMENTS_SETUP.md) - Настройка платежей

### Внешние ресурсы
- [CloudPayments Docs](https://developers.cloudpayments.ru/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram Mini Apps](https://core.telegram.org/bots/webapps)
- [Vertex AI Gemini](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Firestore Docs](https://cloud.google.com/firestore/docs)

## 📄 Лицензия

MIT
