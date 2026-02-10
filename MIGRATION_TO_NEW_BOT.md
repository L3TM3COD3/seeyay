# Миграция на новый Production бот (@seeyay_ai_bot)

## 📋 Что было сделано

### Обновлены имена сервисов Cloud Run:
- `seeyay-bot` → `seeyay-ai-tg-bot`
- `seeyay-api` → `seeyay-ai-api`
- `seeyay-miniapp` → `seeyay-ai-miniapp`

### Обновлены упоминания бота:
- README.md: @seeyay_bot → @seeyay_ai_bot

### Обновлены URL во всех файлах:
- `cloudbuild.yaml` - Cloud Build конфигурация
- `deploy.sh` - скрипт деплоя
- `mini-app/Dockerfile` - Mini App build configuration
- `backend/routers/cron.py` - cron endpoints
- `backend/routers/generate.py` - generation endpoints
- `backend/services/notifications.py` - notification service
- `CLOUDPAYMENTS_SETUP.md` - документация по настройке

## 🔑 Новые данные бота

- **Username**: @seeyay_ai_bot
- **API Token**: `8544304843:AAH4ULG3jHgfdMMFKUqMJqVekfnAx7pAOOA`
- **GCP Project**: seeyay-ai-tg-bot (445810320877)
- **Region**: europe-west4

## ✅ Шаги для завершения миграции

### 1. Обновить секрет telegram-bot-token в Secret Manager

```bash
# Обновляем токен нового бота в Secret Manager
echo -n "8544304843:AAH4ULG3jHgfdMMFKUqMJqVekfnAx7pAOOA" | gcloud secrets versions add telegram-bot-token \
    --data-file=- \
    --project=seeyay-ai-tg-bot
```

### 2. Закоммитить изменения

```bash
# Добавляем измененные файлы
git add .

# Создаем коммит
git commit -m "Migrate to new production bot @seeyay_ai_bot with new Cloud Run service names"

# Пушим в dev ветку
git push origin dev
```

### 3. Мерджим в main и деплоим

```bash
# Переключаемся на main
git checkout main

# Мерджим изменения из dev
git merge dev

# Пушим в main
git push origin main

# Деплоим на production
gcloud builds submit . --config=cloudbuild.yaml --project=seeyay-ai-tg-bot
```

**Примечание**: При первом деплое Cloud Run создаст новые сервисы с новыми именами. Старые сервисы (seeyay-bot, seeyay-api, seeyay-miniapp) можно будет удалить после успешного деплоя.

### 4. Получить URL новых сервисов

```bash
# URL бота
gcloud run services describe seeyay-ai-tg-bot \
    --region=europe-west4 \
    --format='value(status.url)' \
    --project=seeyay-ai-tg-bot

# URL API
gcloud run services describe seeyay-ai-api \
    --region=europe-west4 \
    --format='value(status.url)' \
    --project=seeyay-ai-tg-bot

# URL Mini App
gcloud run services describe seeyay-ai-miniapp \
    --region=europe-west4 \
    --format='value(status.url)' \
    --project=seeyay-ai-tg-bot
```

Ожидаемые URL:
- Bot: `https://seeyay-ai-tg-bot-445810320877.europe-west4.run.app`
- API: `https://seeyay-ai-api-445810320877.europe-west4.run.app`
- Mini App: `https://seeyay-ai-miniapp-445810320877.europe-west4.run.app`

### 5. Настроить бота в @BotFather

1. Откройте [@BotFather](https://t.me/BotFather)
2. Выберите `/mybots`
3. Выберите бота `@seeyay_ai_bot`
4. Перейдите в **Bot Settings** → **Menu Button**
5. Установите URL Mini App:
   ```
   https://seeyay-ai-miniapp-445810320877.europe-west4.run.app
   ```

### 6. Обновить Cloud Scheduler Jobs

Если у вас уже созданы Cloud Scheduler jobs, нужно обновить их URL:

```bash
# Обновить daily-energy job
gcloud scheduler jobs update http daily-energy-job \
    --uri="https://seeyay-ai-api-445810320877.europe-west4.run.app/api/cron/daily-energy" \
    --location=europe-west4 \
    --project=seeyay-ai-tg-bot

# Обновить subscription-retry job
gcloud scheduler jobs update http subscription-retry-job \
    --uri="https://seeyay-ai-api-445810320877.europe-west4.run.app/api/cron/subscription-retry" \
    --location=europe-west4 \
    --project=seeyay-ai-tg-bot

# Обновить subscription-status job
gcloud scheduler jobs update http subscription-status-job \
    --uri="https://seeyay-ai-api-445810320877.europe-west4.run.app/api/cron/subscription-status" \
    --location=europe-west4 \
    --project=seeyay-ai-tg-bot

# Обновить delayed-messages job
gcloud scheduler jobs update http delayed-messages-job \
    --uri="https://seeyay-ai-api-445810320877.europe-west4.run.app/api/cron/delayed-messages" \
    --location=europe-west4 \
    --project=seeyay-ai-tg-bot
```

Если jobs еще не созданы, создайте их согласно инструкции в [CLOUDPAYMENTS_SETUP.md](CLOUDPAYMENTS_SETUP.md).

### 7. Обновить webhook'и CloudPayments (если используются)

Если вы используете custom домен (seeyay.app), убедитесь что он настроен на новый API сервис:

- Check: `https://seeyay.app/api/webhooks/cloudpayments/check`
- Pay: `https://seeyay.app/api/webhooks/cloudpayments/pay`
- Fail: `https://seeyay.app/api/webhooks/cloudpayments/fail`
- Recurrent: `https://seeyay.app/api/webhooks/cloudpayments/recurrent`
- Refund: `https://seeyay.app/api/webhooks/cloudpayments/refund`

Если используете прямой URL Cloud Run без домена, обновите URL в личном кабинете CloudPayments на:
```
https://seeyay-ai-api-445810320877.europe-west4.run.app/api/webhooks/cloudpayments/*
```

### 8. Удалить старые сервисы (опционально)

После успешной работы новых сервисов можно удалить старые:

```bash
# Удаляем старый bot service
gcloud run services delete seeyay-bot \
    --region=europe-west4 \
    --project=seeyay-ai-tg-bot

# Удаляем старый API service
gcloud run services delete seeyay-api \
    --region=europe-west4 \
    --project=seeyay-ai-tg-bot

# Удаляем старый Mini App service
gcloud run services delete seeyay-miniapp \
    --region=europe-west4 \
    --project=seeyay-ai-tg-bot
```

## ✅ Проверка работы

### 1. Проверка бота
- Откройте бота [@seeyay_ai_bot](https://t.me/seeyay_ai_bot)
- Отправьте команду `/start`
- Должно прийти приветственное сообщение с кнопкой Mini App

### 2. Проверка Mini App
- Нажмите на кнопку "🎭 Смотреть все шаблоны"
- Должна открыться галерея шаблонов
- Выберите шаблон
- Проверьте, что сообщение с конфигурацией приходит в чат

### 3. Проверка генерации
- Отправьте фото боту
- Должна начаться генерация с анимацией луны 🌑
- После генерации должно прийти готовое фото

### 4. Проверка платежей (если настроены)
- Откройте Mini App → раздел "Баланс"
- Попробуйте купить пакет энергии
- Проверьте, что платёжная форма открывается

### 5. Проверка логов

```bash
# Логи бота
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-ai-tg-bot" \
    --limit=50 \
    --project=seeyay-ai-tg-bot

# Логи API
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-ai-api" \
    --limit=50 \
    --project=seeyay-ai-tg-bot

# Логи Mini App
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-ai-miniapp" \
    --limit=50 \
    --project=seeyay-ai-tg-bot
```

## 🔄 Откат (если что-то пошло не так)

Если после деплоя возникли проблемы:

1. **Вернуть старый токен бота** (если нужно использовать старого бота):
```bash
echo -n "OLD_BOT_TOKEN" | gcloud secrets versions add telegram-bot-token \
    --data-file=- \
    --project=seeyay-ai-tg-bot
```

2. **Откатить git изменения**:
```bash
git checkout main
git revert HEAD
git push origin main
```

3. **Передеплоить старую версию**:
```bash
gcloud builds submit . --config=cloudbuild.yaml --project=seeyay-ai-tg-bot
```

## 📝 Важные замечания

1. **Dev окружение остается неизменным**: Dev бот (@siay_ai_bot) и dev сервисы (seeyay-bot, seeyay-api, seeyay-miniapp в проекте seeyay-ai-dev) продолжают работать как раньше.

2. **Firestore база данных**: Используется та же база данных, все пользователи и их балансы сохраняются.

3. **Секреты**: Все секреты (CloudPayments, Cron Auth Token) остаются теми же, меняется только telegram-bot-token.

4. **Custom домен**: Если у вас настроен домен seeyay.app, убедитесь что он правильно проксирует запросы на новые сервисы.

## 🎉 Готово!

После выполнения всех шагов ваш новый production бот @seeyay_ai_bot будет полностью настроен и готов к работе!
