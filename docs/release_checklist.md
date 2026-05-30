# Чеклист релізу

## Перевірені вимоги

| Перевірка | Статус |
|---|---|
| Backend запускається без заготовлених користувачів | OK |
| Реєстрація користувача через `POST /api/auth/register` | OK |
| Вхід користувача через `POST /api/auth/login` | OK |
| Додавання контакту за системним номером | OK |
| Створення приватного чату | OK |
| Збереження REST-повідомлення у PostgreSQL | OK |
| Отримання історії повідомлень з PostgreSQL | OK |
| Надсилання повідомлення через WebSocket | OK |
| Публікація події `message.created` у RabbitMQ | OK |
| `notification_worker` читає події з RabbitMQ | OK |
| Для приватного чату запускається серверний `PrivateChatThread` | OK |
| `docker-compose.yml` запускає локальне середовище | OK |
| `docker-compose.server.yml` відкриває назовні тільки frontend/nginx | OK |
| k3s manifests застосовуються в namespace `prosto-chat` | OK |
| k3s pods/services/ingress працюють | OK |
| Релізний архів не містить `.venv`, `.git`, `dist`, `__pycache__`, `.env`, `*.db` | OK |

## Команди перевірки Docker Compose

```powershell
docker compose -p prosto-chat up --build -d
docker compose -p prosto-chat ps
```

Автоматична перевірка через backend:

```powershell
.\.venv\Scripts\python scripts\release_smoke.py
```

Автоматична перевірка через frontend/nginx:

```powershell
$env:API_BASE_URL="http://127.0.0.1:8080/api"
$env:WS_BASE_URL="ws://127.0.0.1:8080/ws"
$env:HEALTH_URL="http://127.0.0.1:8080/health"
.\.venv\Scripts\python scripts\release_smoke.py
```

## Команди перевірки server compose

```powershell
$env:FRONTEND_PORT="8082"
$env:POSTGRES_PASSWORD="server-test-password"
$env:JWT_SECRET="server-test-secret"
docker compose -f docker-compose.server.yml -p prosto-chat-server-test up --build -d

$env:API_BASE_URL="http://127.0.0.1:8082/api"
$env:WS_BASE_URL="ws://127.0.0.1:8082/ws"
$env:HEALTH_URL="http://127.0.0.1:8082/health"
.\.venv\Scripts\python scripts\release_smoke.py

docker compose -f docker-compose.server.yml -p prosto-chat-server-test down -v
```

## Команди перевірки k3s/k3d

```powershell
k3d cluster create prosto-chat-k3s --servers 1 --agents 1 --port "8081:80@loadbalancer" --wait
docker build -t prosto-chat-backend:latest backend
docker build -t prosto-chat-frontend:latest frontend
docker build -t prosto-chat-notification-worker:latest notification_worker
k3d image import prosto-chat-backend:latest prosto-chat-frontend:latest prosto-chat-notification-worker:latest -c prosto-chat-k3s

kubectl apply -f k3s/namespace.yaml
kubectl apply -f k3s/configmap.yaml -f k3s/secrets.yaml -f k3s/services.yaml
kubectl apply -f k3s/postgres-statefulset.yaml -f k3s/rabbitmq-deployment.yaml
kubectl apply -f k3s/backend-deployment.yaml -f k3s/frontend-deployment.yaml -f k3s/notification-worker-deployment.yaml -f k3s/ingress.yaml
kubectl -n prosto-chat get pods,svc,ingress

$env:API_BASE_URL="http://127.0.0.1:8081/api"
$env:WS_BASE_URL="ws://127.0.0.1:8081/ws"
$env:HEALTH_URL="http://127.0.0.1:8081/health"
.\.venv\Scripts\python scripts\release_smoke.py
```

Успішний результат автоматичної перевірки:

```text
RELEASE_SMOKE_OK
```

## Команда створення релізного архіву

```powershell
.\scripts\package_release.ps1
```

Архів створюється у:

```text
dist/prosto-chat-release.zip
```
