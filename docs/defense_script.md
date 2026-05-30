# Сценарій демонстрації викладачу

## 1. Запуск застосунку

```bash
docker compose -f docker-compose.server.yml up --build -d
```

Після запуску відкрити:

- frontend: `http://SERVER_IP/`
- Swagger/OpenAPI: `http://SERVER_IP/docs`
- health check: `http://SERVER_IP/health`

## 2. Показ чистої реєстрації

1. Відкрити головну сторінку.
2. Натиснути «Реєстрація».
3. Створити першого користувача з email або телефоном.
4. Після входу відкрити профіль у правому верхньому куті.
5. Показати унікальний номер користувача формату `PC-000-000`.

## 3. Показ приватних повідомлень

1. У другому браузері або в режимі інкогніто створити другого користувача.
2. Скопіювати номер другого користувача.
3. Повернутися до першого користувача.
4. Відкрити «Контакти».
5. Додати контакт за номером.
6. Створити приватний чат.
7. Надіслати повідомлення.
8. Пояснити, що повідомлення проходить через WebSocket і зберігається в PostgreSQL.

## 4. Показ REST API

Відкрити `http://SERVER_IP/docs` і показати основні endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/me`
- `POST /api/contacts`
- `POST /api/chats/private`
- `GET /api/chats/{chat_id}/messages`
- `POST /api/chats/{chat_id}/messages`
- `WS /ws/chats/{chat_id}`

## 5. Показ Docker Compose

```bash
docker compose -f docker-compose.server.yml ps
```

Пояснити контейнери:

- `frontend` — nginx + web interface;
- `backend` — FastAPI, REST API, WebSocket, потоки чатів;
- `postgres` — база даних;
- `rabbitmq` — AMQP broker;
- `notification_worker` — окремий сервіс для асинхронних подій.

## 6. Показ k3s/k8s

```bash
kubectl -n prosto-chat get pods,svc,ingress
```

Пояснити, що ті самі сервіси винесені в Kubernetes resources: deployments, statefulset, services та ingress.

## 7. Автоматична перевірка

```bash
API_BASE_URL=http://SERVER_IP/api \
WS_BASE_URL=ws://SERVER_IP/ws \
HEALTH_URL=http://SERVER_IP/health \
python scripts/release_smoke.py
```

Скрипт сам створює тимчасових користувачів і завершується `RELEASE_SMOKE_OK`, якщо реєстрація, контакти, приватний чат, БД і WebSocket працюють правильно.
