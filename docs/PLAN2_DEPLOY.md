# Plan 2 Deployment Guide

Инструкции по деплою функционала отложенных сообщений (Plan 2) на dev окружение.

## Что было реализовано в Plan 2

✅ **1. Firestore поля для delayed-сообщений**
- `started_at`, `template_selected_at`, `last_generation_at`
- `m2_sent`, `m5_sent`, `m10_1_sent`, `m10_2_sent`, `m12_sent`
- `m9_sent_at`, `any_pack_purchased`

✅ **2. Запись timestamp'ов**
- `started_at` → при `/start` (только для новых пользователей)
- `template_selected_at` → при выборе шаблона
- `last_generation_at` → после успешной генерации
- `m9_sent_at` → при показе m9

✅ **3. Клавиатуры для backend**
- `backend/keyboards_raw.py` — dict-формат для HTTP API

✅ **4. Cron endpoint**
- `POST /api/cron/delayed-messages` — обрабатывает все 5 delayed-сообщений

✅ **5. Методы отправки в NotificationService**
- `send_m2_reminder()`, `send_m5_photo_reminder()`
- `send_m10_1_tips()`, `send_m10_2_pro_suggestion()`
- `send_m12_downsell()`

✅ **6. Анимация emoji луны в m6**
- Фоновая asyncio задача с циклом 🌑🌘🌗🌖🌕🌔🌓🌒

✅ **7. Инфраструктура для медиа**
- Поле `cover_image` в стилях (для будущих фото обложек)
- Условная логика отправки фото/текста в handlers

---

## Шаг 1: Деплой на dev окружение

### 1.1. Проверка изменений

```bash
cd c:\PetProjects\Seeyay.ai

# Проверяем измененные файлы
git status
```

**Измененные файлы:**
- `bot/firestore.py` — новые поля + `set_user_timestamp()`
- `bot/handlers/start.py` — запись `started_at`
- `bot/handlers/template_selection.py` — запись `template_selected_at`, cover_image логика
- `bot/handlers/photo.py` — запись `last_generation_at`, `m9_sent_at`, moon emoji animation
- `bot/messages.py` — обновлен m1_welcome() с video_file_id
- `bot/styles_data.py` — добавлено поле `cover_image`
- `backend/firestore.py` — новые поля + `get_users_for_delayed_messages()`
- `backend/routers/cron.py` — новый endpoint `/delayed-messages`
- `backend/services/notifications.py` — 5 новых методов для delayed-сообщений

**Новые файлы:**
- `backend/keyboards_raw.py` — клавиатуры для backend

### 1.2. Commit и push

```bash
# Коммит изменений
git add .
git commit -m "Implement Plan 2: delayed messages, emoji animation, media infrastructure"

# Push в ветку dev
git push origin dev
```

### 1.3. Деплой через Cloud Build

```bash
# Деплой на seeyay-ai-dev
gcloud builds submit . --config=cloudbuild-dev.yaml --project=seeyay-ai-dev
```

**Проверка деплоя:**
1. Дождитесь завершения билда (~5-10 минут)
2. Проверьте логи: [Cloud Build Console](https://console.cloud.google.com/cloud-build/builds?project=seeyay-ai-dev)
3. Проверьте, что все 3 сервиса запущены:
   - `seeyay-bot` (бот)
   - `seeyay-api` (backend API)
   - `seeyay-miniapp` (Mini App)

---

## Шаг 2: Настройка Cloud Scheduler

Создаем новый cron job для отправки delayed-сообщений.

### 2.1. Определяем URL backend API

```bash
# Получаем URL backend API
gcloud run services describe seeyay-api \
    --region=europe-west4 \
    --project=seeyay-ai-dev \
    --format='value(status.url)'
```

**Пример вывода:**
```
https://seeyay-api-269162169877.europe-west4.run.app
```

### 2.2. Создаем Cloud Scheduler job

```bash
# Замените BACKEND_API_URL на фактический URL из предыдущего шага
BACKEND_API_URL="https://seeyay-api-269162169877.europe-west4.run.app"

gcloud scheduler jobs create http delayed-messages \
    --location=europe-west4 \
    --schedule="*/2 * * * *" \
    --uri="${BACKEND_API_URL}/api/cron/delayed-messages" \
    --http-method=POST \
    --headers="Authorization=Bearer dev-cron-token" \
    --project=seeyay-ai-dev \
    --description="Send delayed messages (m2, m5, m10.1, m10.2, m12) every 2 minutes"
```

**Параметры:**
- `--schedule="*/2 * * * *"` — каждые 2 минуты
- `--uri` — endpoint для delayed-сообщений
- `--headers` — авторизация (пока простой токен)

### 2.3. Проверка создания job

```bash
# Список всех cron jobs
gcloud scheduler jobs list --location=europe-west4 --project=seeyay-ai-dev
```

**Ожидаемый вывод:**
```
ID                LOCATION        SCHEDULE (TZ)         TARGET_TYPE  STATE
daily-energy      europe-west4    0 0 * * * (UTC)      HTTP         ENABLED
delayed-messages  europe-west4    */2 * * * * (UTC)    HTTP         ENABLED
...
```

### 2.4. Ручной запуск для теста

```bash
# Запустить delayed-messages job вручную
gcloud scheduler jobs run delayed-messages \
    --location=europe-west4 \
    --project=seeyay-ai-dev
```

---

## Шаг 3: Тестирование delayed-сообщений

### 3.1. Тест m2 (через 1 час после /start)

**Условия:** `started_at + 1h < now` AND `successful_generations == 0` AND `m2_sent == False`

**Тест:**
1. Откройте dev бота: [@siay_ai_bot](https://t.me/siay_ai_bot)
2. Отправьте `/start`
3. **НЕ ДЕЛАЙТЕ генерацию** (чтобы `successful_generations == 0`)
4. Измените `started_at` в Firestore вручную (поставьте -2 часа от текущего времени)
5. Подождите следующий запуск cron (до 2 минут)
6. **Ожидаемый результат:** получите m2 с текстом "Ты в одном шаге от фото мечты!"

**Firestore update (для ускорения теста):**
```javascript
// В Firestore Console: users/<telegram_id>
{
  "started_at": new Date(Date.now() - 2 * 60 * 60 * 1000) // -2 часа
}
```

### 3.2. Тест m5 (через 7 мин после выбора шаблона)

**Условия:** `template_selected_at + 7min < now` AND `successful_generations < 3` AND `m5_sent == False`

**Тест:**
1. Выберите любой шаблон
2. **НЕ ОТПРАВЛЯЙТЕ фото**
3. Измените `template_selected_at` в Firestore (-10 минут)
4. Подождите cron запуск
5. **Ожидаемый результат:** получите m5 с текстом "Ты ещё тут? 👀"

### 3.3. Тест m10.1 (через 60 мин после 1-й генерации)

**Условия:** `last_generation_at + 60min < now` AND `successful_generations == 1` AND `m10_1_sent == False`

**Тест:**
1. Сделайте 1 успешную генерацию
2. Измените `last_generation_at` в Firestore (-65 минут)
3. Подождите cron запуск
4. **Ожидаемый результат:** получите m10.1 с советами

### 3.4. Тест m10.2 (через 60 мин после 2-й генерации)

**Условия:** `last_generation_at + 60min < now` AND `successful_generations == 2` AND `m10_2_sent == False`

**Тест:**
1. Сделайте 2 успешных генерации
2. Измените `last_generation_at` (-65 минут)
3. Подождите cron запуск
4. **Ожидаемый результат:** получите m10.2 с предложением PRO-режима

### 3.5. Тест m12 (через 24ч после m9)

**Условия:** `m9_sent_at + 24h < now` AND `any_pack_purchased == False` AND `m12_sent == False`

**Тест:**
1. Получите m9 (попытка генерации без баланса, новый пользователь, 1+ генераций)
2. Измените `m9_sent_at` в Firestore (-25 часов)
3. **НЕ ПОКУПАЙТЕ пакеты** (чтобы `any_pack_purchased == False`)
4. Подождите cron запуск
5. **Ожидаемый результат:** получите m12 с downsell предложением (8⚡ за 169₽)

---

## Шаг 4: Проверка логов

### 4.1. Логи cron job

```bash
# Логи Cloud Scheduler
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_name=delayed-messages" \
    --limit=20 \
    --project=seeyay-ai-dev \
    --format=json
```

### 4.2. Логи backend API

```bash
# Логи cron endpoint
gcloud logging read "resource.type=cloud_run_revision \
    AND resource.labels.service_name=seeyay-api \
    AND textPayload=~'delayed.*messages'" \
    --limit=50 \
    --project=seeyay-ai-dev
```

**Что искать в логах:**
- `"Delayed messages job completed"` — успешное выполнение
- `"m2": {"sent": 1, ...}` — количество отправленных m2
- `"Error sending m2 to user"` — ошибки отправки

### 4.3. Логи бота

```bash
# Логи бота (для проверки timestamp записей)
gcloud logging read "resource.type=cloud_run_revision \
    AND resource.labels.service_name=seeyay-bot \
    AND textPayload=~'timestamp'" \
    --limit=30 \
    --project=seeyay-ai-dev
```

**Что искать:**
- `"New user ... - started_at recorded"`
- `"last_generation_at"` — запись после генерации

---

## Шаг 5: Тестирование emoji-анимации

### 5.1. Тест moon emoji animation в m6

**Тест:**
1. Выберите шаблон
2. Отправьте фото
3. **Ожидаемое поведение:** 
   - Сообщение "Генерируем ваше фото..." появляется с emoji 🌑
   - Emoji меняется каждую секунду: 🌑 → 🌘 → 🌗 → 🌖 → 🌕 → 🌔 → 🌓 → 🌒 → (цикл повторяется)
   - После завершения генерации (~30 сек) сообщение удаляется

**Если анимация не работает:**
- Проверьте логи бота на ошибки `"Moon animation edit error"`
- Убедитесь, что asyncio задача создается и останавливается корректно

---

## Шаг 6: Finalize

### 6.1. Проверка всех функций

**Чек-лист:**
- ✅ m2 отправляется через 1ч после /start (без генераций)
- ✅ m5 отправляется через 7 мин после выбора шаблона (без фото)
- ✅ m10.1 отправляется через 60 мин после 1-й генерации
- ✅ m10.2 отправляется через 60 мин после 2-й генерации
- ✅ m12 отправляется через 24ч после m9 (без покупок)
- ✅ Emoji анимация работает в m6
- ✅ Timestamp'ы записываются корректно

### 6.2. Отключение тестового cron (опционально)

Если хотите временно отключить cron:

```bash
# Приостановить job
gcloud scheduler jobs pause delayed-messages \
    --location=europe-west4 \
    --project=seeyay-ai-dev

# Возобновить позже
gcloud scheduler jobs resume delayed-messages \
    --location=europe-west4 \
    --project=seeyay-ai-dev
```

---

## Известные ограничения

1. **Медиа-ассеты не готовы:** Поля `cover_image` и `video_file_id` пока `None`. Когда будут готовы файлы:
   - Загрузите фото/видео в бот
   - Получите `file_id` из Telegram
   - Обновите `bot/styles_data.py`

2. **Авторизация cron:** Сейчас используется простой Bearer токен `"dev-cron-token"`. В production нужен безопасный токен из Secret Manager.

3. **Mini App URL:** Хардкодный URL в `cron.py`. Лучше вынести в переменную окружения.

---

## Troubleshooting

### Проблема: delayed-сообщения не отправляются

**Решение:**
1. Проверьте, что cron job запущен: `gcloud scheduler jobs list`
2. Проверьте логи cron: `gcloud logging read "resource.type=cloud_scheduler_job"`
3. Проверьте, что backend API доступен
4. Проверьте Firestore — правильно ли установлены timestamp'ы

### Проблема: emoji-анимация не работает

**Решение:**
1. Проверьте логи бота на ошибки редактирования сообщения
2. Убедитесь, что asyncio задача создается и stop_event устанавливается
3. Попробуйте увеличить sleep до 1.5 сек (если Telegram rate limit)

### Проблема: импорты bot.messages в backend

**Решение:**
- Убедитесь, что `sys.path.insert()` работает корректно
- В Docker контейнере пути должны быть относительно `/app/`

---

## Следующие шаги

После успешного тестирования на dev:

1. **Merge в main:**
   ```bash
   git checkout main
   git merge dev
   git push origin main
   ```

2. **Деплой на production:**
   ```bash
   gcloud builds submit . --config=cloudbuild.yaml --project=seeyay-ai
   ```

3. **Создать Cloud Scheduler на production:**
   - Повторите шаги из Шаг 2, но для проекта `seeyay-ai`
   - Используйте безопасный токен из Secret Manager

4. **Загрузить медиа-ассеты:**
   - Подготовьте видео для m1 (intro)
   - Подготовьте фото обложек для m2, m3, m4.x
   - Обновите `bot/styles_data.py` с file_id'ами

---

## Контакты

Если возникли проблемы при деплое — проверьте:
- [Cloud Build Logs](https://console.cloud.google.com/cloud-build/builds?project=seeyay-ai-dev)
- [Cloud Run Services](https://console.cloud.google.com/run?project=seeyay-ai-dev)
- [Cloud Scheduler Jobs](https://console.cloud.google.com/cloudscheduler?project=seeyay-ai-dev)
- [Firestore Console](https://console.firebase.google.com/project/seeyay-ai-dev/firestore)
