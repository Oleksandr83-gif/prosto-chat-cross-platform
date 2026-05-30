# Розгортання на Ubuntu/Hetzner

Цей документ описує запуск готового release-пакета «Просто Чат» на Ubuntu-сервері. Застосунок запускається з чистою базою даних: користувачі створюються через реєстрацію у web-інтерфейсі або через REST API.

## 1. Встановити Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl unzip
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo ${UBUNTU_CODENAME:-$VERSION_CODENAME}) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

За потреби додати поточного користувача до групи `docker`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 2. Розпакувати release

```bash
mkdir -p ~/prosto-chat
cd ~/prosto-chat
unzip prosto-chat-release.zip
```

Якщо архів розпаковано у вкладену папку, перейти в неї:

```bash
cd prosto-chat-release
```

## 3. Налаштувати `.env`

```bash
cp .env.example .env
nano .env
```

Обов'язково змінити паролі та JWT secret:

```env
FRONTEND_PORT=80
POSTGRES_DB=chat_db
POSTGRES_USER=chat
POSTGRES_PASSWORD=<strong-postgres-password>
JWT_SECRET=<long-random-jwt-secret>
```

## 4. Запустити server compose

```bash
docker compose -f docker-compose.server.yml up --build -d
```

Server compose відкриває назовні тільки `frontend/nginx`. Backend, PostgreSQL і RabbitMQ доступні всередині Docker-мережі. Nginx проксирує:

- `/api/...` до backend REST API;
- `/ws/...` до backend WebSocket;
- `/docs` до Swagger/OpenAPI;
- `/health` до backend health check;
- `/media/...` до завантажених файлів.

## 5. Перевірити запуск

```bash
docker compose -f docker-compose.server.yml ps
curl http://127.0.0.1/health
```

У браузері:

- `http://SERVER_IP/`
- `http://SERVER_IP/docs`
- `http://SERVER_IP/health`

## 6. Створити першого користувача

1. Відкрити `http://SERVER_IP/`.
2. Натиснути «Реєстрація».
3. Вказати ім'я, email або телефон і пароль.
4. Після входу відкрити профіль у правому верхньому куті.
5. Скопіювати системний номер користувача для пошуку в контактах.

## 7. Автоматична перевірка

Автоматичну перевірку можна запустити з сервера або з локальної машини. Скрипт сам створює тимчасових користувачів і не потребує підготовленої БД.

```bash
API_BASE_URL=http://SERVER_IP/api \
WS_BASE_URL=ws://SERVER_IP/ws \
HEALTH_URL=http://SERVER_IP/health \
python scripts/release_smoke.py
```

Успішний результат:

```text
RELEASE_SMOKE_OK
```

## 8. Логи

```bash
docker compose -f docker-compose.server.yml logs -f backend
docker compose -f docker-compose.server.yml logs -f notification_worker
docker compose -f docker-compose.server.yml logs -f frontend
```

## 9. Зупинка

```bash
docker compose -f docker-compose.server.yml down
```

З видаленням БД і завантажених файлів:

```bash
docker compose -f docker-compose.server.yml down -v
```
