# EventHub

A Django backend for discovering and booking events — built with real-time seat locking, async notifications, and payment processing.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5, Django REST Framework |
| Auth | djangorestframework-simplejwt |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Task Queue | Celery |
| Real-time | Django Channels, WebSockets |
| Payments | Razorpay |
| Containerization | Docker, Docker Compose |

---

## Project Structure

```
EventHub/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── asgi.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/
├── events/
├── payments/
├── notifications/
├── docker-compose.yml
├── Dockerfile
├── manage.py
└── requirements.txt
```

---

## Apps

| App | Responsibility |
|---|---|
| `accounts` | Custom user model, JWT auth, login/logout/signup |
| `events` | Event listing, seat management, booking |
| `payments` | Razorpay integration, webhooks, idempotency |
| `notifications` | Multi-channel notifications, WebSocket consumer |

---

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Run the project

```bash
# Clone the repo
git clone https://github.com/your-username/EventHub.git
cd EventHub

# Start all services
docker compose up --build

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser
```

### Services

| Service | URL |
|---|---|
| Django API | http://localhost:8000 |
| Django Admin | http://localhost:8000/admin |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## Environment Variables

Create a `.env` file in the root directory:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://postgres:postgres@db:5432/eventhub
REDIS_URL=redis://redis:6379/0
DJANGO_SETTINGS_MODULE=config.settings.dev
```

---

## Development

### Run Celery worker

```bash
docker compose exec web celery -A config worker -l info
```

### Open Django shell

```bash
docker compose exec web python manage.py shell
```

### Make migrations

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Run tests

```bash
docker compose exec web pytest
```

---

## API Endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/accounts/signup/` | Register new user |
| POST | `/api/accounts/login/` | Login, returns JWT |
| POST | `/api/accounts/logout/` | Logout, clears cookie |
| POST | `/api/accounts/token/refresh/` | Refresh access token |

---

## Notification Channels

| Channel | Provider | Status |
|---|---|---|
| In-App | Django Channels + Redis | ✅ Live |
| Email | SendGrid / AWS SES | 🔲 Stubbed |
| SMS | TBD | 🔲 Stubbed |
| WhatsApp | Meta Cloud API | 🔲 Stubbed |

---

## License

MIT