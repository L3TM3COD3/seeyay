# Troubleshooting Guide

Документация по решению проблем, возникающих при разработке и деплое проекта.

## 🖥️ Проблемы Mini App

### 1. Mini App показывает бесконечную загрузку

#### Проблема
После открытия Mini App через кнопку в боте приложение показывает экран загрузки (loading spinner) и остается на нем навсегда, контент не отображается.

#### Симптомы
- Кнопка "🎭 Смотреть все шаблоны" в боте работает и открывает Mini App
- Mini App открывается в Telegram WebView
- Показывается спиннер загрузки, но приложение не переходит к основному контенту
- В консоли браузера (если доступна) могут быть ошибки сети или отсутствие данных пользователя

#### Причина
В компоненте `App.tsx` при загрузке данных пользователя через `fetchUser()`:
- Если API возвращает `null` (пользователь не найден) или запрос выбрасывает ошибку
- Функция `setUser()` не вызывается
- Состояние `user` остается `null`
- Приложение застревает на проверке `if (!user)` и показывает загрузку навсегда

```typescript
// Проблемный код:
useEffect(() => {
  if (isReady && tgUser) {
    fetchUser(tgUser.id).then((userData) => {
      if (userData) {
        setUser(userData);
      }
      // ПРОБЛЕМА: если userData === null, setUser не вызывается
    });
  }
}, [isReady, tgUser]);
```

#### Решение

Добавьте fallback механизмы в `mini-app/src/App.tsx`:

```typescript
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
    setUser({
      id: 1,
      telegram_id: 123456789,
      username: 'test_user',
      plan: 'free',
      balance: 100
    });
  }
}, [isReady, tgUser]);
```

#### Как проверить
1. Откройте бот в Telegram
2. Нажмите кнопку открытия Mini App
3. Приложение должно загрузиться и показать галерею шаблонов (без бесконечной загрузки)

#### Как избежать в будущем
- Всегда добавляйте fallback для API запросов, которые блокируют UI
- Обрабатывайте случаи `null`/`undefined` и ошибки сети
- Используйте `.catch()` для всех промисов, которые влияют на состояние загрузки
- Добавьте таймаут для загрузки данных с переходом в fallback режим

---

## 🚀 Проблемы при деплое на Dev стенд

### 1. Bot возвращает 503 "Bot not initialized" на все webhook запросы

#### Проблема
После деплоя бот не реагирует на `/start` и другие команды. Логи показывают:
```
POST /webhook HTTP/1.1" 503 188 "-" "-"
```

При проверке health endpoint контейнер здоров и отвечает 200 OK, но webhook endpoints возвращают 503.

#### Причина
Бот не может инициализироваться из-за ошибки импорта в одном из модулов handlers. В нашем случае:
```
ImportError: cannot import name 'get_photo_request_keyboard' from 'bot.keyboards'
```

Проблема была в файле `bot/handlers/webapp.py` — он импортировал функцию, которая была удалена при рефакторинге `bot/keyboards.py` в Plan 1. Сам файл `webapp.py` был obsolete, так как его функционал уже был перенесён в `bot/handlers/template_selection.py`.

#### Решение

**1. Добавьте детальное логирование** в `bot/main.py` для диагностики:
```python
async def init_bot(app):
    try:
        logger.info("=== Initializing bot ===")
        sys.stdout.flush()
        
        logger.info("Importing aiogram...")
        sys.stdout.flush()
        from aiogram import Bot, Dispatcher
        # ... и т.д. для каждого импорта
        
        logger.info("All imports successful!")
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"=== FAILED to initialize bot: {e} ===", exc_info=True)
        sys.stdout.flush()
```

**2. Проверьте логи после деплоя:**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-bot" \
    --project=seeyay-ai-dev \
    --limit=30 \
    --format="value(textPayload)"
```

**3. Найдите ImportError в логах** и исправьте проблему:
- Удалите obsolete файлы (`bot/handlers/webapp.py`)
- Удалите импорты из `bot/handlers/__init__.py`
- Удалите импорты из `bot/main.py`

**4. Перезадеплойте:**
```bash
gcloud builds submit . --config=cloudbuild-dev.yaml --project=seeyay-ai-dev
```

#### Как избежать в будущем
- При рефакторинге всегда проверяйте, какие файлы импортируют изменённые модули
- Используйте `grep` для поиска всех импортов удаляемых функций:
  ```bash
  grep -r "from bot.keyboards import" bot/handlers/
  ```
- Добавьте в CI/CD проверку импортов через `python -m py_compile`

---

### 2. TypeScript ошибки при сборке Mini App

#### Проблема
При деплое через `cloudbuild-dev.yaml` сборка Mini App падала с TypeScript ошибками:

```
src/App.tsx(169,11): error TS2719: Type '(tab: TabId) => void' is not assignable to type '(tab: TabId) => void'. 
  Two different types with this name exist, but they are unrelated.
  Types of parameters 'tab' and 'tab' are incompatible.
    Type 'TabId' is not assignable to type 'TabId'. Two different types with this name exist, but they are unrelated.
      Type '"energy"' is not assignable to type 'TabId'.

src/components/Profile.tsx(11,7): error TS6133: 'planNames' is declared but its value is never read.

src/pages/EnergyPage.tsx(233,29): error TS6133: 'index' is declared but its value is never read.
```

#### Причина
1. **Конфликт типов `TabId`**: В `BottomNavigation.tsx` тип `TabId` содержал старое значение `'energy'`, которое уже было удалено из `App.tsx` при рефакторинге навигации.
2. **Неиспользуемые переменные**: После рефакторинга остались неиспользуемые переменные, которые TypeScript помечает как ошибки в строгом режиме.

#### Решение

**Файл `mini-app/src/components/BottomNavigation.tsx`:**
```typescript
// Было:
type TabId = 'photo-ideas' | 'profile' | 'energy';

// Стало:
type TabId = 'photo-ideas' | 'profile';
```

**Файл `mini-app/src/components/Profile.tsx`:**
```typescript
// Удалена неиспользуемая константа
const planNames: Record<string, string> = {
  free: 'Free',
  basic: 'Basic',
  pro: 'Pro',
};
```

**Файл `mini-app/src/pages/EnergyPage.tsx`:**
```typescript
// Было:
{packs.map((pack, index) => {

// Стало:
{packs.map((pack) => {
```

### 3. Отсутствие прав Cloud Run для деплоя

#### Проблема
При деплое Cloud Build не мог задеплоить сервисы на Cloud Run:

```
ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Permission 'run.services.get' denied on resource 
'namespaces/seeyay-ai-dev/services/seeyay-bot' (or resource may not exist). 
This command is authenticated as 269162169877-compute@developer.gserviceaccount.com which is 
the active account specified by the [core/account] property.
```

#### Причина
Сервисному аккаунту Cloud Build (`269162169877-compute@developer.gserviceaccount.com`) не были выданы права на управление сервисами Cloud Run.

#### Решение
```bash
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member=serviceAccount:269162169877-compute@developer.gserviceaccount.com \
    --role=roles/run.admin
```

**Важно:** Эта роль дает полный доступ к управлению сервисами Cloud Run, включая создание, обновление и удаление.

### 4. Отсутствие прав Service Account User

#### Проблема
После добавления `roles/run.admin` возникла новая ошибка:

```
ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Permission 'iam.serviceaccounts.actAs' denied on 
service account 269162169877-compute@developer.gserviceaccount.com (or it may not exist). 
This command is authenticated as 269162169877-compute@developer.gserviceaccount.com which is 
the active account specified by the [core/account] property.
```

#### Причина
Cloud Run сервисы запускаются от имени сервисного аккаунта. Для этого Cloud Build должен иметь право "действовать от имени" (`actAs`) этого сервисного аккаунта.

#### Решение
```bash
gcloud iam service-accounts add-iam-policy-binding \
    269162169877-compute@developer.gserviceaccount.com \
    --member=serviceAccount:269162169877-compute@developer.gserviceaccount.com \
    --role=roles/iam.serviceAccountUser \
    --project=seeyay-ai-dev
```

**Альтернативный способ** (на уровне проекта):
```bash
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member=serviceAccount:269162169877@cloudbuild.gserviceaccount.com \
    --role=roles/iam.serviceAccountUser
```

---

## 📋 Checklist для настройки нового dev окружения

Используйте этот checklist при создании нового dev окружения с нуля:

### 1. Создание GCP проекта
```bash
gcloud projects create seeyay-ai-dev --name="СИЯЙ AI Dev"
gcloud config set project seeyay-ai-dev
```

### 2. Включение необходимых API
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    cloudscheduler.googleapis.com
```

### 3. Создание Firestore базы данных
```bash
gcloud firestore databases create --location=europe-west4
```

### 4. Получение номера проекта
```bash
PROJECT_NUMBER=$(gcloud projects describe seeyay-ai-dev --format="value(projectNumber)")
echo "Project Number: $PROJECT_NUMBER"
```

### 5. Выдача прав Cloud Build сервисному аккаунту

#### Основные права для работы с GCP сервисами:
```bash
# Cloud Build Builder (для сборки образов)
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.builder"

# Cloud Run Admin (для деплоя сервисов)
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/run.admin"

# Service Account User (для actAs)
gcloud iam service-accounts add-iam-policy-binding \
    ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" \
    --project=seeyay-ai-dev

# Firestore User (для работы с БД)
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/datastore.user"

# Secret Manager Accessor (для чтения секретов)
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Vertex AI User (для генерации)
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Storage Admin (для работы с GCS)
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.admin"

# Logging (для записи логов)
gcloud projects add-iam-policy-binding seeyay-ai-dev \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/logging.logWriter"
```

### 6. Создание секретов

#### Telegram Bot Token (получите у @BotFather для dev бота)
```bash
echo -n "YOUR_DEV_BOT_TOKEN" | gcloud secrets create telegram-bot-token \
    --data-file=- --replication-policy="automatic" --project=seeyay-ai-dev
```

#### CloudPayments Public ID (test)
```bash
echo -n "test_api_xxx" | gcloud secrets create cloudpayments-public-id \
    --data-file=- --replication-policy="automatic" --project=seeyay-ai-dev
```

#### CloudPayments API Secret (test)
```bash
echo -n "test_secret_xxx" | gcloud secrets create cloudpayments-api-secret \
    --data-file=- --replication-policy="automatic" --project=seeyay-ai-dev
```

#### Cron Auth Token
```bash
openssl rand -base64 32 | gcloud secrets create cron-auth-token \
    --data-file=- --replication-policy="automatic" --project=seeyay-ai-dev
```

### 7. Первый деплой
```bash
gcloud builds submit . --config=cloudbuild-dev.yaml --project=seeyay-ai-dev
```

---

## ⏰ Проблемы с Delayed Messages

### Delayed messages (m2, m5, m10.1 и т.д.) не приходят

#### Возможные причины:

1. **`started_at` не установлен** 
   - m2 требует `started_at != None`. Проверьте, что `/start` устанавливает это поле
   - После сброса пользователя через скрипт нужно обязательно выполнить `/start` заново

2. **Условия не выполнены** 
   - Каждое сообщение имеет свои условия по времени и состоянию пользователя
   - Проверьте код в `backend/firestore.py` → функция `get_users_for_delayed_messages()`

3. **Флаг уже установлен** 
   - `m2_sent=True` означает, что сообщение уже было отправлено
   - Нужно сбросить флаг через Firestore Console или скрипт

#### Диагностика состояния пользователя

Проверьте логи Cloud Run для конкретного пользователя:

```bash
gcloud logging read "resource.type=cloud_run_revision AND textPayload:<USER_TELEGRAM_ID>" \
    --project=seeyay-ai-tg-bot --limit=20
```

Проверьте состояние пользователя в Firestore Console:
```
https://console.cloud.google.com/firestore/data/users/<USER_TELEGRAM_ID>?project=seeyay-ai-tg-bot
```

Ключевые поля для проверки:
- `started_at` — должен быть установлен (не `None`)
- `successful_generations` — должен быть `0` для m2
- `m2_sent` — должен быть `False` для m2
- `last_generation_at` — должен быть установлен для m10.1/m10.2
- `m10_1_sent` / `m10_2_sent` — должны быть `False`

#### Таймеры delayed messages (production):

| Сообщение | Таймер | Условие |
|-----------|--------|---------|
| m2 | 1 час после `/start` | `successful_generations == 0` |
| m5 | 7 минут после выбора шаблона | `successful_generations < 3` |
| m10.1 | 60 минут после генерации | `successful_generations == 1` |
| m10.2 | 60 минут после генерации | `successful_generations == 2` |
| m12 | 24 часа после m9 | `any_pack_purchased == False` |

---

## 🎨 Проблемы с генерацией изображений

### Генерация изображений не работает (403 Permission Denied)

#### Проблема
После отправки фото в бот генерация падает с ошибкой `403 Permission 'aiplatform.endpoints.predict' denied`.

#### Причина
Service account Cloud Run не имеет прав доступа к Vertex AI.

#### Решение

Выдайте роль `roles/aiplatform.user` сервисному аккаунту:

```bash
gcloud projects add-iam-policy-binding seeyay-ai-tg-bot \
    --member="serviceAccount:445810320877-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

#### Проверка

После выдачи прав **обязательно** выполните редеплой бота для применения изменений:

```bash
gcloud builds submit --config=cloudbuild.yaml --project=seeyay-ai-tg-bot
```

Или принудительно обновите сервис:

```bash
gcloud run services update seeyay-ai-tg-bot \
    --region=europe-west4 \
    --project=seeyay-ai-tg-bot
```

---

## 🗄️ Проблемы с Firestore

### Локальные скрипты работают с неправильным Firestore

#### Проблема
Локальные Python скрипты (например, для сброса пользователей) выполняются успешно, но изменения не видны в production. Данные пользователей остаются прежними.

#### Причина
`firestore.AsyncClient()` без явного указания project ID использует default проект из `gcloud config`, который может отличаться от production проекта.

```python
# НЕПРАВИЛЬНО - использует default проект из gcloud config
from google.cloud import firestore
db = firestore.AsyncClient()
```

#### Решение

**ВСЕГДА** явно указывайте project ID при создании Firestore клиента:

```python
# ПРАВИЛЬНО - явно указываем production проект
from google.cloud import firestore
db = firestore.AsyncClient(project="seeyay-ai-tg-bot")
```

#### Проверка текущего default проекта

```bash
gcloud config get-value project
```

Если это не `seeyay-ai-tg-bot`, то локальные скрипты без явного указания проекта будут работать с другой базой данных.

#### Пример правильного скрипта сброса

```python
"""
Reset user to initial state
Usage: python reset_user.py <telegram_id>
"""
import asyncio
import sys
from google.cloud import firestore

async def reset_user(user_id: str):
    # ВАЖНО: Явно указываем проект
    PROJECT_ID = "seeyay-ai-tg-bot"
    db = firestore.AsyncClient(project=PROJECT_ID)
    
    doc_ref = db.collection("users").document(user_id)
    
    reset_data = {
        "balance": 3,
        "successful_generations": 0,
        "is_new_user": True,
        "started_at": None,
        "m2_sent": False,
        "m5_sent": False,
        "m10_1_sent": False,
        "m10_2_sent": False,
        # ... другие поля
    }
    
    await doc_ref.update(reset_data)
    print(f"User {user_id} reset in project {PROJECT_ID}")

if __name__ == "__main__":
    asyncio.run(reset_user(sys.argv[1]))
```

---

## 🔍 Общие проблемы и решения

### Webhook'и CloudPayments не приходят

#### Проблема
После оплаты CloudPayments не отправляет webhook на сервер, платежи не обрабатываются.

#### Возможные причины и решения:

1. **Проверьте URL в настройках CloudPayments**
   - Зайдите в личный кабинет CloudPayments
   - Убедитесь, что webhook URL указан правильно: `https://seeyay-ai-api-445810320877.europe-west4.run.app/api/webhooks/cloudpayments`
   - URL должен быть доступен по HTTPS

2. **Проверьте доступность домена**
   ```bash
   curl -X POST https://seeyay-ai-api-445810320877.europe-west4.run.app/api/webhooks/cloudpayments \
       -H "Content-Type: application/json" \
       -d '{}'
   ```

3. **Проверьте логи Cloud Run API**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-ai-api" \
       --project=seeyay-ai-tg-bot --limit=50
   ```

### Ошибка проверки подписи CloudPayments

#### Проблема
Webhook от CloudPayments приходит, но сервер отклоняет его с ошибкой проверки подписи.

#### Решение:

1. **Убедитесь, что API Secret правильно сохранен в Secret Manager**
   ```bash
   gcloud secrets versions access latest --secret=cloudpayments-api-secret --project=seeyay-ai-tg-bot
   ```

2. **Проверьте кодировку (UTF-8)**
   - API Secret должен быть сохранен в UTF-8 без BOM
   - При создании секрета используйте `echo -n` (без переноса строки)

3. **Проверьте код проверки подписи**
   - См. `backend/services/cloudpayments.py` → метод `verify_signature()`

### Cron jobs не выполняются

#### Проблема
Cloud Scheduler не вызывает cron endpoints, delayed messages не отправляются.

#### Диагностика:

1. **Проверьте расписание Cloud Scheduler**
   ```bash
   gcloud scheduler jobs list --location=europe-west1 --project=seeyay-ai-tg-bot
   ```

2. **Проверьте, что Cloud Run API доступен**
   ```bash
   curl https://seeyay-ai-api-445810320877.europe-west4.run.app/health
   ```

3. **Проверьте авторизацию**
   - Убедитесь, что `cron-auth-token` существует в Secret Manager
   - Проверьте, что Bearer token передаётся в заголовке Authorization
   - Код проверки: `backend/routers/cron.py` → функция `verify_cron_auth()`

4. **Проверьте логи Cloud Scheduler**
   ```bash
   gcloud logging read "resource.type=cloud_scheduler_job" \
       --project=seeyay-ai-tg-bot --limit=20
   ```

5. **Проверьте логи cron endpoint**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-ai-api AND textPayload:delayed-messages" \
       --project=seeyay-ai-tg-bot --limit=20
   ```

#### Если cron job возвращает 401 Unauthorized:

Проверьте, что API имеет доступ к секрету `cron-auth-token`:

```bash
gcloud projects add-iam-policy-binding seeyay-ai-tg-bot \
    --member="serviceAccount:445810320877-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Ошибка: "invalid reference format" при сборке Docker образа

#### Проблема
```
invalid argument "gcr.io/project-id/image-name:" for "-t, --tag" flag: invalid reference format
```

#### Причина
Переменная для тега Docker образа (например, `$COMMIT_SHA`) не разрешается, создавая пустой тег.

#### Решение
- Используйте только статичные теги типа `:latest` для dev окружения
- Для production используйте `$COMMIT_SHA` через Cloud Build substitutions

### Ошибка: "could not resolve build arg"

#### Проблема
Docker не может получить build arg из Cloud Build.

#### Решение
В `cloudbuild-dev.yaml` убедитесь, что build args передаются правильно:

```yaml
- name: 'gcr.io/cloud-builders/docker'
  args:
    - 'build'
    - '--build-arg'
    - 'VITE_API_URL=https://seeyay-api-xxx.run.app'
    - '-t'
    - 'gcr.io/$PROJECT_ID/seeyay-miniapp:latest'
    - '-f'
    - 'mini-app/Dockerfile'
    - 'mini-app'
```

### Проверка логов Cloud Run

```bash
# Последние 50 логов API
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-api" \
    --project=seeyay-ai-dev \
    --limit=50 \
    --format=json

# Последние 50 логов Bot
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-bot" \
    --project=seeyay-ai-dev \
    --limit=50

# Логи Mini App
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-miniapp" \
    --project=seeyay-ai-dev \
    --limit=50
```

### Проверка статуса Cloud Build

```bash
# Список последних билдов
gcloud builds list --project=seeyay-ai-dev --limit=5

# Детали конкретного билда
gcloud builds describe BUILD_ID --project=seeyay-ai-dev

# Логи билда
gcloud builds log BUILD_ID --project=seeyay-ai-dev
```

### Проверка сервисов Cloud Run

```bash
# Список сервисов
gcloud run services list --project=seeyay-ai-dev --region=europe-west4

# Детали сервиса
gcloud run services describe seeyay-api \
    --project=seeyay-ai-dev \
    --region=europe-west4

# Последняя ревизия
gcloud run revisions list \
    --project=seeyay-ai-dev \
    --region=europe-west4 \
    --service=seeyay-api \
    --limit=1
```

---

## 🐛 Известные проблемы

### TypeScript strict mode в Mini App

**Проблема:** При включенном strict mode TypeScript ловит больше ошибок (неиспользуемые переменные, несовместимость типов).

**Решение:** 
- Всегда удаляйте неиспользуемые импорты и переменные
- Синхронизируйте типы между компонентами
- Используйте `npm run build` локально перед деплоем для проверки

### Несинхронизированные типы между файлами

**Проблема:** TypeScript типы (например, `TabId`) определяются в нескольких файлах и могут рассинхронизироваться.

**Рекомендация:** Вынесите общие типы в отдельный файл `types.ts`:

```typescript
// mini-app/src/types.ts
export type TabId = 'photo-ideas' | 'profile';
export type Screen = TabId | 'settings';
// ... другие общие типы
```

Затем импортируйте везде:
```typescript
import { TabId, Screen } from './types';
```

---

## 📞 Поддержка

Если столкнулись с проблемой, которая не описана в этом руководстве:

1. Проверьте логи Cloud Run и Cloud Build
2. Убедитесь, что все IAM права выданы правильно
3. Проверьте, что все секреты созданы и доступны
4. Для TypeScript ошибок запустите `npm run build` локально
5. Обратитесь к основному [README.md](README.md) для общей информации о проекте
