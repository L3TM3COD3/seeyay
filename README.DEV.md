# 🔧 Development Environment

Инструкция по работе с dev окружением для безопасной разработки и тестирования.

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Repository                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   main branch (Production)     dev branch (Development)     │
│   ├── .env                     ├── .env.dev                 │
│   ├── GCP: seeyay-ai-tg-bot    ├── GCP: seeyay-ai-dev       │
│   └── Real users               └── Test data only           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Быстрый старт

### 1. Настройка GCP проекта для разработки (один раз)

```bash
# Создать проект
gcloud projects create seeyay-ai-dev --name="Seeyay AI Development"

# Включить бесплатный Firestore API
gcloud services enable firestore.googleapis.com --project=seeyay-ai-dev

# Создать Firestore
gcloud firestore databases create --location=europe-west4 --project=seeyay-ai-dev

# Настроить ADC
gcloud auth application-default login
gcloud config set project seeyay-ai-dev
gcloud auth application-default set-quota-project seeyay-ai-dev
```

> **📝 Примечание:** Для использования Vertex AI и Cloud Run нужно привязать биллинг к проекту:
> 1. Откройте https://console.cloud.google.com/billing/linkedaccount?project=seeyay-ai-dev
> 2. Привяжите billing account
> 3. Затем включите API:
> ```bash
> gcloud services enable aiplatform.googleapis.com cloudbuild.googleapis.com run.googleapis.com --project=seeyay-ai-dev
> ```

### 2. Создать dev бота в Telegram (один раз)

1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Назовите его (например: "СИЯЙ AI Dev Bot")
4. Скопируйте токен

### 3. Создать .env.dev

```env
BOT_TOKEN=your_dev_bot_token_from_botfather
GCP_PROJECT_ID=seeyay-ai-dev
GCP_LOCATION=europe-west4
BACKEND_URL=http://localhost:8000
MINI_APP_URL=http://localhost:3000
CLOUDPAYMENTS_PUBLIC_ID=test_api_xxx
CLOUDPAYMENTS_API_SECRET=test_secret_xxx
USE_POLLING=true
```

> **Важно:** `USE_POLLING=true` включает polling режим для локальной разработки. Без этого бот не будет реагировать на команды!

### 4. Запуск

```bash
# Убедитесь что вы на dev ветке
git checkout dev

# Убедитесь что ADC настроен на dev проект
gcloud config get-value project
# Должно быть: seeyay-ai-dev

# Запуск backend + bot
python run_dev_env.py

# В отдельном терминале: запуск Mini App
cd mini-app
npm install  # первый раз
npm run dev
```

> **📱 Mini App:** запускается отдельно на http://localhost:3000. При нажатии кнопки "Выбрать стиль (dev)" в боте вы увидите URL для открытия в браузере (Telegram не поддерживает HTTP для WebApp кнопок).

## Workflow разработки

### Разработка новой функции

```bash
# 1. Переключиться на dev ветку
git checkout dev

# 2. Убедиться что используется dev проект
gcloud config set project seeyay-ai-dev

# 3. Разрабатывать и тестировать
python run_dev_env.py

# 4. Коммитить изменения
git add .
git commit -m "feat: описание изменений"
```

### Деплой в production

```bash
# 1. Убедиться что всё работает в dev
git checkout dev
python run_dev_env.py
# ... тестирование ...

# 2. Переключиться на main
git checkout main

# 3. Влить изменения из dev
git merge dev

# 4. Переключить GCP на production
gcloud config set project seeyay-ai-tg-bot

# 5. Задеплоить
./deploy.sh

# 6. Вернуться в dev для дальнейшей разработки
git checkout dev
gcloud config set project seeyay-ai-dev
```

## Полная изоляция

### Что изолировано

| Компонент | Production | Development |
|-----------|------------|-------------|
| GCP Project | seeyay-ai-tg-bot | seeyay-ai-dev |
| Firestore | Real users | Test data |
| Telegram Bot | @YourProdBot | @YourDevBot |
| Git Branch | main | dev |
| Config File | .env | .env.dev |

### Преимущества

- ✅ **Полная изоляция данных** - разные Firestore базы
- ✅ **Безопасное тестирование** - невозможно затронуть real users
- ✅ **Чистая история** - dev коммиты отдельно от prod
- ✅ **Независимые боты** - разные токены, разные чаты
- ✅ **Откат** - можно всегда вернуться к stable main

## Переключение между окружениями

### Быстрый чеклист

```bash
# Переключиться на dev
git checkout dev
gcloud config set project seeyay-ai-dev
python run_dev_env.py

# Переключиться на production (для деплоя)
git checkout main
gcloud config set project seeyay-ai-tg-bot
./deploy.sh
```

### Проверить текущее окружение

```bash
# Текущая ветка
git branch --show-current

# Текущий GCP проект
gcloud config get-value project
```

## Технические нюансы

### Polling vs Webhook

- **Production (Cloud Run)**: Бот использует webhook — Telegram отправляет updates на URL
- **Local dev**: Бот использует polling — сам запрашивает updates у Telegram

Переключение контролируется переменной `USE_POLLING=true` в `.env.dev`.

### HTTP vs HTTPS для Mini App

Telegram требует **HTTPS** для WebApp кнопок. Для локальной разработки с `http://localhost:3000` используется обходное решение:

- Кнопка показывается как `"Выбрать стиль (dev)"`
- При нажатии бот отправляет URL для открытия в браузере вручную
- В production с HTTPS всё работает как обычная WebApp кнопка

### Структура запущенных сервисов

```
┌────────────────────────────────────────────────────────────┐
│                     Local Development                       │
├────────────────────────────────────────────────────────────┤
│  Terminal 1: python run_dev_env.py                         │
│  ├── Backend (FastAPI) → http://localhost:8000             │
│  └── Bot (aiogram polling) → @YourDevBot                   │
│                                                            │
│  Terminal 2: cd mini-app && npm run dev                    │
│  └── Mini App (Vite) → http://localhost:3000               │
└────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Бот не отвечает на /start

1. Проверьте что `USE_POLLING=true` в `.env.dev`
2. Перезапустите `python run_dev_env.py`
3. В логах должно быть: `Webhook deleted, will use polling mode`

### "Permission denied" при доступе к Firestore/Vertex AI

```bash
# Убедитесь что ADC настроен
gcloud auth application-default login

# Убедитесь что проект правильный
gcloud config set project seeyay-ai-dev
```

### "Bot token invalid"

Убедитесь что в `.env.dev` правильный токен dev бота (не production).

### Изменения не применяются

```bash
# Убедитесь что вы на правильной ветке
git branch --show-current

# Если нужно - переключитесь
git checkout dev
```

## Структура файлов dev ветки

```
Seeyay.ai/
├── .env.dev              # Dev конфигурация (не в git)
├── run_dev_env.py        # Скрипт запуска dev окружения
├── README.DEV.md         # Эта документация
└── ... остальные файлы
```

## Полезные команды

```bash
# Статус
git status
gcloud config list

# Логи Cloud Run (если задеплоили в dev)
gcloud logging read "resource.type=cloud_run_revision" --project=seeyay-ai-dev --limit=50

# Firestore консоль
# https://console.cloud.google.com/firestore?project=seeyay-ai-dev
```
