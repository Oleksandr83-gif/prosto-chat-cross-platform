# Просто Чат

«Просто Чат» — кросплатформений застосунок для обміну приватними повідомленнями. Проєкт складається з frontend-інтерфейсу, FastAPI backend, PostgreSQL, WebSocket-каналу, окремих серверних потоків приватних чатів, RabbitMQ/AMQP worker, Docker Compose та k3s/k8s manifests.

Проєкт запускається з чистою базою даних. Користувачі створюються тільки через реєстрацію у застосунку або через REST API.

## Виконані вимоги

| Вимога практичної роботи | Реалізація у проєкті |
|---|---|
| Збереження повідомлень у БД | PostgreSQL, SQLAlchemy models, таблиця `messages` |
| Особисті повідомлення | Приватні чати типу `private` |
| Окремий потік для кожного приватного чату | `PrivateChatThread` і `ThreadManager` на стороні backend |
| Socket-технологія | WebSocket endpoint `WS /ws/chats/{chat_id}` |
| REST API для контролерів | FastAPI routes `/api/auth`, `/api/users`, `/api/contacts`, `/api/chats`, `/api/files` |
| MVC/MVVM підхід | Розділення на `models`, `schemas`, `routers`, `services`, frontend view/state |
| AMQP і мікросервісна комунікація | RabbitMQ exchange `chat.events` і окремий `notification_worker` |
| Docker/Podman контейнеризація | `docker-compose.yml` і `docker-compose.server.yml` |
| k3s/k8s розміщення | YAML manifests у каталозі `k3s/` |
| Автентифікація користувача | JWT registration/login |

## Локальний запуск через Docker Compose

```bash
docker compose -p prosto-chat up --build -d
```

Після запуску:

- frontend: `http://localhost:8080`
- backend OpenAPI: `http://localhost:8000/docs`
- health check: `http://localhost:8000/health`
- RabbitMQ management: `http://localhost:15672`

Перший користувач створюється через кнопку «Реєстрація» на стартовому екрані. Після реєстрації застосунок показує системний номер користувача формату `PC-000-000`, за яким інші користувачі можуть додати його в контакти.

## Запуск на Ubuntu/Hetzner

На сервері використовується окремий compose-файл, де назовні відкрито тільки frontend/nginx на порту 80. Backend, PostgreSQL і RabbitMQ залишаються всередині Docker-мережі.

```bash
unzip prosto-chat-release.zip
cp .env.example .env
nano .env
docker compose -f docker-compose.server.yml up --build -d
```

Детальна інструкція: `docs/deploy_ubuntu.md`.

## k3s/k8s

Manifests знаходяться в каталозі `k3s/`.

Локальна перевірка через k3d:

```bash
k3d cluster create prosto-chat-k3s --servers 1 --agents 1 --port "8081:80@loadbalancer" --wait
docker build -t prosto-chat-backend:latest backend
docker build -t prosto-chat-frontend:latest frontend
docker build -t prosto-chat-notification-worker:latest notification_worker
k3d image import prosto-chat-backend:latest prosto-chat-frontend:latest prosto-chat-notification-worker:latest -c prosto-chat-k3s
kubectl apply -f k3s/namespace.yaml
kubectl apply -f k3s/configmap.yaml -f k3s/secrets.yaml -f k3s/services.yaml
kubectl apply -f k3s/postgres-statefulset.yaml -f k3s/rabbitmq-deployment.yaml
kubectl apply -f k3s/backend-deployment.yaml -f k3s/frontend-deployment.yaml -f k3s/notification-worker-deployment.yaml -f k3s/ingress.yaml
```

Перевірка:

```bash
kubectl -n prosto-chat get pods,svc,ingress
```

## Автоматична перевірка

Автоматична перевірка не потребує підготовлених користувачів. Скрипт сам реєструє двох тимчасових користувачів через REST API, додає контакт, створює приватний чат, зберігає повідомлення в БД і перевіряє WebSocket.

```bash
python scripts/release_smoke.py
```

Для перевірки через frontend/nginx:

```bash
API_BASE_URL=http://SERVER_IP/api \
WS_BASE_URL=ws://SERVER_IP/ws \
HEALTH_URL=http://SERVER_IP/health \
python scripts/release_smoke.py
```

## Документація для здачі

- `docs/project_report.md` — опис роботи для викладача.
- `docs/defense_script.md` — короткий сценарій демонстрації.
- `docs/deploy_ubuntu.md` — інструкція розгортання на Ubuntu.
- `docs/release_checklist.md` — список технічних перевірок перед релізом.
