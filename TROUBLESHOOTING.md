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

## 🔍 Общие проблемы и решения

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
