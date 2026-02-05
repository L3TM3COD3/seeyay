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
- 🎨 Галерея стилей фотосессий с категориями
- 👤 Профиль пользователя с балансом энергии (⚡)
- 🖼️ Генерация фото в стиле (Обычный = 1⚡, PRO = 2⚡)
- 📜 История генераций
- 💡 Автоматическое списание и возврат энергии

### Платежная система
- 💳 **Покупка пакетов энергии** (единоразово)
  - 10⚡ = 99₽
  - 30⚡ = 249₽
  - 100⚡ = 699₽
- 🔄 **Подписки с автопродлением**
  - Free: 1⚡ в день (бесплатно)
  - Basic: 30⚡/мес. за 499₽
  - PRO: 150⚡/мес. за 1299₽
- 🏦 **Оплата через СБП** (QR-код + deeplink)
- 📱 **Онлайн-чеки** (54-ФЗ) через CloudKassir
- 🔁 **Автоматические retry** при неудачных платежах
- 🎁 **Win-back скидки 25%** для возврата подписчиков

## 📁 Структура проекта

```
Seeyay.ai/
├── bot/                       # Telegram бот (aiogram)
│   ├── Dockerfile         
│   ├── handlers/              # Обработчики команд
│   │   ├── start.py          # /start команда
│   │   ├── photo.py          # Обработка фото + списание энергии
│   │   └── webapp.py         # Web App данные
│   ├── services/              # Сервисы
│   │   └── vertex_ai.py      # Генерация через Vertex AI
│   ├── firestore.py           # Firestore операции
│   └── main.py            
│
├── backend/                   # FastAPI сервер
│   ├── Dockerfile         
│   ├── routers/               # API endpoints
│   │   ├── styles.py         # Стили
│   │   ├── users.py          # Пользователи
│   │   ├── payments.py       # Платежи и подписки
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
│   │   │   ├── Profile.tsx
│   │   │   ├── PaymentModal.tsx   # CloudPayments виджет
│   │   │   └── ...
│   │   ├── pages/
│   │   │   └── EnergyPage.tsx     # Покупка энергии/подписок
│   │   └── api/
│   │       └── client.ts          # API клиент
│   └── ...
│
├── cloudbuild.yaml            # CI/CD конфигурация
├── cloudbuild-dev.yaml        # CI/CD для dev окружения
├── deploy.sh                  # Скрипт деплоя
├── CLOUDPAYMENTS_SETUP.md     # Инструкции по настройке платежей
├── TROUBLESHOOTING.md         # Решение типичных проблем
└── requirements.txt       
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

```bash
# Деплой на production (seeyay-ai)
gcloud builds submit . --config=cloudbuild.yaml --project=seeyay-ai
```

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

# 2. Вносим изменения, тестируем локально
python run_dev.py

# 3. Деплоим на dev окружение
gcloud builds submit . --config=cloudbuild-dev.yaml --project=seeyay-ai-dev

# 4. Тестируем в dev боте (@siay_ai_dev_bot)

# 5. Когда всё ОК — мержим в main и деплоим на prod
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

## 💻 Локальная разработка

> **🔧 Development Environment:** Для безопасной разработки используйте отдельную **dev ветку** с изолированным GCP проектом. См. `README.DEV.md` в dev ветке.
>
> ```bash
> git checkout dev          # Переключиться на dev ветку
> python run_dev_env.py     # Запустить dev окружение
> ```

### 1. Настройка окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Конфигурация

Создайте файл `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=europe-west4
BACKEND_URL=http://localhost:8000
MINI_APP_URL=http://localhost:3000
CLOUDPAYMENTS_PUBLIC_ID=test_api_xxx
CLOUDPAYMENTS_API_SECRET=test_secret_xxx
```

> **💡 Важно:** Проект использует Vertex AI с ADC (Application Default Credentials). Настройте один раз:
> ```bash
> gcloud auth application-default login
> gcloud config set project your-gcp-project-id
> ```

### 3. Аутентификация GCP

```bash
# Для локальной разработки
gcloud auth application-default login
```

### 4. Запуск

```bash
# Backend
python -m uvicorn backend.main:app --reload --port 8000

# Bot
python -m bot.main

# Mini App
cd mini-app
npm install
npm run dev
```

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

### Подписки

| Тариф | Цена | Энергия | Описание |
|-------|------|---------|----------|
| **Free** | 0₽/мес. | 1⚡ в день | Обновляется каждый день в 00:00 МСК |
| **Basic** | 499₽/мес. | 30⚡/мес. | Обновляется при следующей оплате |
| **PRO** | 1299₽/мес. | 150⚡/мес. | Обновляется при следующей оплате |

### Пакеты энергии (единоразово)

| Пакет | Цена | Энергия |
|-------|------|---------|
| Маленький | 99₽ | 10⚡ |
| Средний | 249₽ | 30⚡ |
| Большой | 699₽ | 100⚡ |

### Стоимость генерации

- **Обычный режим**: 1⚡ за 1 фото
- **PRO режим**: 2⚡ за 1 фото

## 🔄 Логика подписок

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
  "plan": "basic",           // free | basic | pro
  "balance": 30,              // текущая энергия
  "subscription": {
    "status": "active",       // active | grace | suspended | canceled | expired
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
  "product": "pack_10 | basic | pro",
  "amount": 499,
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
