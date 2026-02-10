# CloudPayments Integration Setup Guide

Этот документ содержит инструкции по настройке интеграции CloudPayments для проекта Seeyay.ai.

## 1. Регистрация в CloudPayments

1. Зарегистрируйтесь на [CloudPayments](https://cloudpayments.ru)
2. Получите **Public ID** и **API Secret** в личном кабинете
3. Подключите онлайн-кассу CloudKassir
4. Заключите договор с оператором фискальных данных (ОФД)

## 2. Создание секретов в Google Secret Manager

Выполните следующие команды для создания секретов:

```bash
# Public ID
echo -n "your_public_id_here" | gcloud secrets create cloudpayments-public-id \
    --data-file=- \
    --replication-policy="automatic"

# API Secret  
echo -n "your_api_secret_here" | gcloud secrets create cloudpayments-api-secret \
    --data-file=- \
    --replication-policy="automatic"

# Дайте права на чтение секретов для Cloud Run
gcloud secrets add-iam-policy-binding cloudpayments-public-id \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding cloudpayments-api-secret \
    --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## 3. Настройка домена для webhook'ов

CloudPayments требует HTTPS для webhook'ов. Настройте домен seeyay.app:

1. Создайте Load Balancer в GCP
2. Настройте DNS A-record для seeyay.app
3. Получите SSL сертификат (Google Managed Certificate)
4. Настройте backend service для Cloud Run API

Либо используйте простой вариант - настройте домен напрямую на Cloud Run service.

## 4. Настройка webhook'ов в CloudPayments

В личном кабинете CloudPayments настройте следующие URL для уведомлений:

- **Check**: `https://seeyay.app/api/webhooks/cloudpayments/check`
- **Pay**: `https://seeyay.app/api/webhooks/cloudpayments/pay`
- **Fail**: `https://seeyay.app/api/webhooks/cloudpayments/fail`
- **Recurrent**: `https://seeyay.app/api/webhooks/cloudpayments/recurrent`
- **Refund**: `https://seeyay.app/api/webhooks/cloudpayments/refund`

Метод: **POST**  
Кодировка: **UTF-8**  
Формат: **JSON**

## 5. Настройка Cloud Scheduler Jobs

### 5.1 Daily Energy Job (ежедневное начисление энергии)

```bash
gcloud scheduler jobs create http daily-energy-job \
    --schedule="0 21 * * *" \
    --time-zone="UTC" \
    --uri="https://seeyay-ai-api-445810320877.europe-west4.run.app/api/cron/daily-energy" \
    --http-method=POST \
    --headers="Authorization=Bearer YOUR_CRON_AUTH_TOKEN" \
    --location=europe-west4
```

**Расписание**: Каждый день в 21:00 UTC (00:00 по МСК)

### 5.2 Subscription Retry Job (повторные попытки оплаты)

```bash
gcloud scheduler jobs create http subscription-retry-job \
    --schedule="*/30 * * * *" \
    --time-zone="UTC" \
    --uri="https://seeyay-ai-api-445810320877.europe-west4.run.app/api/cron/subscription-retry" \
    --http-method=POST \
    --headers="Authorization=Bearer YOUR_CRON_AUTH_TOKEN" \
    --location=europe-west4
```

**Расписание**: Каждые 30 минут

### 5.3 Subscription Status Job (обновление статусов подписок)

```bash
gcloud scheduler jobs create http subscription-status-job \
    --schedule="0 * * * *" \
    --time-zone="UTC" \
    --uri="https://seeyay-ai-api-445810320877.europe-west4.run.app/api/cron/subscription-status" \
    --http-method=POST \
    --headers="Authorization=Bearer YOUR_CRON_AUTH_TOKEN" \
    --location=europe-west4
```

**Расписание**: Каждый час

### 5.4 Генерация токена авторизации для cron jobs

Для безопасности создайте токен авторизации:

```bash
# Сгенерируйте случайный токен
openssl rand -base64 32

# Сохраните токен в Secret Manager
echo -n "your_generated_token" | gcloud secrets create cron-auth-token \
    --data-file=- \
    --replication-policy="automatic"

# Обновите backend/routers/cron.py чтобы проверять этот токен
```

## 6. Тестирование интеграции

### 6.1 Тестовая среда CloudPayments

CloudPayments предоставляет тестовый режим. Используйте тестовые карты:

- **Успешная оплата**: `4242 4242 4242 4242`
- **Отклоненная оплата**: `4000 0000 0000 0002`
- **3-D Secure**: `4000 0000 0000 3220`

CVV: любой (например, 123)  
Срок действия: любая будущая дата

### 6.2 Проверка webhook'ов

После настройки webhook'ов сделайте тестовый платеж и проверьте логи:

```bash
# Логи Cloud Run API
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seeyay-api" \
    --limit=50 \
    --format=json
```

### 6.3 Проверка cron jobs

```bash
# Проверить статус jobs
gcloud scheduler jobs list --location=europe-west4

# Запустить job вручную
gcloud scheduler jobs run daily-energy-job --location=europe-west4

# Посмотреть логи выполнения
gcloud logging read "resource.type=cloud_scheduler_job" \
    --limit=50 \
    --format=json
```

## 7. Мониторинг и алерты

Настройте алерты в Google Cloud Monitoring для:

- Ошибок webhook'ов (status code 4xx, 5xx)
- Неудачных платежей
- Провалившихся cron jobs
- Низкого баланса у пользователей на платных тарифах

## 8. Безопасность

### 8.1 Проверка подписи webhook'ов

Webhook'и от CloudPayments подписаны HMAC-SHA256. Код проверки уже реализован в `backend/routers/webhooks.py`.

### 8.2 Rate Limiting

Настройте rate limiting для защиты API:

```yaml
# В Cloud Armor или API Gateway
rateLimit:
  maxRequests: 100
  intervalSeconds: 60
```

### 8.3 Firewall Rules

Ограничьте доступ к cron endpoints только с IP Cloud Scheduler или используйте токены авторизации.

## 9. Поддержка пользователей

Для обработки запросов на возврат:

1. Пользователь пишет в поддержку
2. Администратор проверяет платеж в CloudPayments
3. Выполняет возврат через личный кабинет CloudPayments или API
4. Webhook автоматически обновит баланс пользователя

## 10. Troubleshooting

### Проблема: Webhook не приходит

- Проверьте URL в настройках CloudPayments
- Убедитесь, что домен доступен по HTTPS
- Проверьте логи Cloud Run

### Проблема: Ошибка проверки подписи

- Убедитесь, что API Secret правильно сохранен в Secret Manager
- Проверьте кодировку (должна быть UTF-8)

### Проблема: Cron job не выполняется

- Проверьте расписание: `gcloud scheduler jobs describe JOB_NAME --location=europe-west4`
- Убедитесь, что Cloud Run API доступен
- Проверьте права доступа

## 11. Полезные ссылки

- [Документация CloudPayments](https://developers.cloudpayments.ru/)
- [CloudPayments API](https://developers.cloudpayments.ru/#api)
- [Рекуррентные платежи](https://developers.cloudpayments.ru/#rekurrentnye-platezhi)
- [СБП](https://developers.cloudpayments.ru/#sbp)
- [54-ФЗ (онлайн-касса)](https://developers.cloudpayments.ru/#54-fz)
- [Google Cloud Scheduler](https://cloud.google.com/scheduler/docs)
