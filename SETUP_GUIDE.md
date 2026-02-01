# 🚀 Пошаговая инструкция по запуску СИЯЙ AI

**Ваш проект:** `seeyay-ai-tg-bot`  
**Регион:** `europe-west4`

---

## ✅ Что уже сделано

- [x] Проект GCP создан
- [x] API включены
- [x] Service account создан
- [x] Права на Vertex AI выданы
- [x] Секрет telegram-bot-token создан
- [x] Firestore настроен (шаг 2)
- [x] Права service account выданы (шаг 3)
- [x] Бот задеплоен (шаг 5) → https://seeyay-bot-445810320877.europe-west4.run.app
- [x] API задеплоен (шаг 6) → https://seeyay-api-445810320877.europe-west4.run.app
- [x] Mini App задеплоен (шаг 7) → https://seeyay-miniapp-445810320877.europe-west4.run.app

---

## ~~Шаг 2: Настроить Firestore (база данных)~~ ✅ ВЫПОЛНЕНО

<details>
<summary>Показать команды (уже выполнено)</summary>

```powershell
gcloud config set project seeyay-ai-tg-bot
gcloud firestore databases create --location=europe-west4
```
</details>

---

## ~~Шаг 3: Дать права service account~~ ✅ ВЫПОЛНЕНО

<details>
<summary>Показать команды (уже выполнено)</summary>

```powershell
gcloud secrets add-iam-policy-binding telegram-bot-token --member="serviceAccount:seeyay-run-sa@seeyay-ai-tg-bot.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

```powershell
gcloud projects add-iam-policy-binding seeyay-ai-tg-bot --member="serviceAccount:seeyay-run-sa@seeyay-ai-tg-bot.iam.gserviceaccount.com" --role="roles/datastore.user"
```
</details>

---

## ~~Шаг 4: Перейти в папку проекта~~ ✅ ВЫПОЛНЕНО

Проект перенесён в: `C:\PetProjects\Seeyay.ai`

```powershell
cd "C:\PetProjects\Seeyay.ai"
```

---

## ~~Шаг 5: Собрать и задеплоить БОТА~~ ✅ ВЫПОЛНЕНО

**URL бота:** https://seeyay-bot-445810320877.europe-west4.run.app

<details>
<summary>Показать команды (уже выполнено)</summary>

```powershell
gcloud builds submit --tag europe-west4-docker.pkg.dev/seeyay-ai-tg-bot/seeyay/bot bot
```

```powershell
gcloud run deploy seeyay-bot --image europe-west4-docker.pkg.dev/seeyay-ai-tg-bot/seeyay/bot --region europe-west4 --platform managed --memory 512Mi --min-instances 1 --max-instances 3 --set-env-vars "GCP_PROJECT_ID=seeyay-ai-tg-bot,GCP_LOCATION=europe-west4" --set-secrets "BOT_TOKEN=telegram-bot-token:latest" --service-account seeyay-run-sa@seeyay-ai-tg-bot.iam.gserviceaccount.com --allow-unauthenticated
```
</details>

---

## ~~Шаг 6: Собрать и задеплоить API~~ ✅ ВЫПОЛНЕНО

**URL API:** https://seeyay-api-445810320877.europe-west4.run.app

<details>
<summary>Показать команды (уже выполнено)</summary>

```powershell
gcloud builds submit --tag europe-west4-docker.pkg.dev/seeyay-ai-tg-bot/seeyay/api backend
```

```powershell
gcloud run deploy seeyay-api --image europe-west4-docker.pkg.dev/seeyay-ai-tg-bot/seeyay/api --region europe-west4 --platform managed --memory 1Gi --min-instances 0 --max-instances 10 --set-env-vars "GCP_PROJECT_ID=seeyay-ai-tg-bot" --service-account seeyay-run-sa@seeyay-ai-tg-bot.iam.gserviceaccount.com --allow-unauthenticated
```
</details>

---

## ~~Шаг 7: Собрать и задеплоить Mini App~~ ✅ ВЫПОЛНЕНО

**URL Mini App:** https://seeyay-miniapp-445810320877.europe-west4.run.app

<details>
<summary>Показать команды (уже выполнено)</summary>

```powershell
cd "C:\PetProjects\Seeyay.ai\mini-app"
npm install
npm run build
cd ..
gcloud builds submit --tag europe-west4-docker.pkg.dev/seeyay-ai-tg-bot/seeyay/miniapp mini-app
gcloud run deploy seeyay-miniapp --image europe-west4-docker.pkg.dev/seeyay-ai-tg-bot/seeyay/miniapp --region europe-west4 --platform managed --memory 256Mi --min-instances 0 --max-instances 5 --allow-unauthenticated
```
</details>

---

## ~~Шаг 8: Получить URL сервисов~~ ✅ ВЫПОЛНЕНО

📝 **URL Mini App для BotFather:** `https://seeyay-miniapp-445810320877.europe-west4.run.app`

---

## Шаг 9: Настроить бота в Telegram

1. Откройте Telegram
2. Найдите **@BotFather**
3. Напишите `/mybots`
4. Выберите вашего бота
5. Нажмите **Bot Settings**
6. Нажмите **Menu Button**
7. Нажмите **Configure menu button**
8. Отправьте URL Mini App (из шага 8)
9. Отправьте текст: `✨ Выбрать стиль`

---

## Шаг 10: Проверить!

1. Откройте вашего бота в Telegram
2. Напишите `/start`
3. Должно появиться приветствие
4. Нажмите кнопку меню — должен открыться Mini App

---

## 🆘 Если что-то не работает

### Посмотреть логи бота:
```powershell
gcloud run services logs read seeyay-bot --region europe-west4 --limit 50
```

### Посмотреть логи API:
```powershell
gcloud run services logs read seeyay-api --region europe-west4 --limit 50
```

### Частые проблемы:

| Проблема | Решение |
|----------|---------|
| "Permission denied" | Проверьте права service account (шаг 3) |
| "Secret not found" | Имя секрета должно быть `telegram-bot-token` |
| "Image not found" | Используйте путь `europe-west4-docker.pkg.dev/...` вместо `gcr.io/...` |
| Бот не отвечает | Проверьте что токен в секрете правильный |
| Build failed | Посмотрите ошибки в выводе команды |

---

## ✅ Готово!

Если всё работает — поздравляю! 🎉

Ваш бот готов к использованию.
