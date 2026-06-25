# EventHub

A Django backend for discovering and booking events — built with real-time seat locking, async notifications, payment processing, and semantic search.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5, Django REST Framework |
| Auth | djangorestframework-simplejwt, django-allauth (Google OAuth) |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Task Queue | Celery + Celery Beat |
| Real-time | Django Channels, WebSockets, Daphne (ASGI) |
| Payments | Razorpay |
| Search | LangChain, ChromaDB, sentence-transformers |
| Containerization | Docker, Docker Compose |
| API Docs | drf-spectacular (Swagger UI) |
| Testing | pytest, pytest-django |
| CI | GitHub Actions |

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
│   ├── celery.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/
│   ├── adapters.py        # Google OAuth role assignment
│   ├── models.py          # Custom user with role + phone_number
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── events/
│   ├── models.py          # Event, Seat, Booking
│   ├── lock_service.py    # Redis distributed seat locking
│   ├── embedding_service.py  # ChromaDB + LangChain semantic search
│   ├── signals.py         # Auto-index events on save
│   ├── tasks.py           # Celery Beat lock expiry task
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── payments/
│   ├── models.py          # Payment, WebhookEvent
│   ├── services.py        # Razorpay order creation
│   ├── views.py           # Order creation + webhook handler
│   └── urls.py
├── notifications/
│   ├── models.py          # Notification model
│   ├── strategies.py      # Email, SMS, WhatsApp, InApp channels
│   ├── factory.py         # Channel factory
│   ├── tasks.py           # Celery async dispatcher
│   ├── signals.py         # Observer — fires on booking events
│   ├── consumers.py       # WebSocket consumer
│   └── routing.py
├── frontend/
│   ├── views.py           # All template views
│   └── urls.py
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── accounts/
│   ├── events/
│   ├── bookings/
│   ├── payments/
│   ├── notifications/
│   ├── organizer/
│   └── socialaccount/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_events.py
│   └── test_notifications.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker-compose.yml
├── Dockerfile
├── manage.py
└── requirements.txt
```

---

## Apps

| App | Responsibility |
|---|---|
| `accounts` | Custom user model, JWT auth, Google OAuth via allauth |
| `events` | Event listing, seat locking, booking, semantic search |
| `payments` | Razorpay integration, webhooks, idempotency |
| `notifications` | Multi-channel notifications, WebSocket consumer |
| `frontend` | Django template views, role-based UI |

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

# Index existing events into ChromaDB
docker compose exec web python manage.py index_events
```

### Services

| Service | URL |
|---|---|
| Frontend | http://localhost:8000 |
| Django Admin | http://localhost:8000/admin |
| Swagger API Docs | http://localhost:8000/api/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## Environment Variables

Create a `.env` file in the root directory:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.dev

# Database
DB_NAME=eventhub_db
DB_USER=eventhub_user
DB_PASSWORD=your-db-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your-secret
RAZORPAY_WEBHOOK_SECRET=your-webhook-secret

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# WhatsApp (Meta Cloud API — stubbed)
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
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

### Index events into ChromaDB

```bash
docker compose exec web python manage.py index_events
```

### Run tests

```bash
docker compose exec web pytest tests/ -v
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
| GET | `/accounts/google/login/` | Google OAuth login |

### Events

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/events/` | List all published events |
| GET | `/api/events/<id>/` | Event detail with seats |
| GET | `/api/events/search/?q=query` | Semantic search |
| POST | `/api/events/seats/<id>/lock/` | Lock a seat (Redis) |
| POST | `/api/events/seats/<id>/release/` | Release a seat lock |
| POST | `/api/events/seats/<id>/book/` | Confirm booking |
| GET | `/api/events/bookings/my/` | My bookings |

### Payments

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/payments/orders/<booking_id>/` | Create Razorpay order |
| POST | `/api/payments/webhook/` | Razorpay webhook handler |

### Docs

| URL | Description |
|---|---|
| `/api/docs/` | Swagger UI |
| `/api/schema/` | OpenAPI 3.0 schema |

---

## Key Features

### Redis Distributed Seat Locking
Seats are locked atomically using Redis `SET NX EX` — a single operation that guarantees only one user can hold a seat at a time, even under heavy concurrent load. Locks expire after 10 minutes. A Celery Beat task runs every 60 seconds to clean up expired locks.

### Semantic Search
Events are indexed into ChromaDB as vector embeddings using the `all-MiniLM-L6-v2` sentence transformer model. Users can search in plain English — "music night under 500 rupees" — and get semantically relevant results even if the exact words don't appear in the event title.

### Real-time WebSockets
In-app notifications are pushed instantly via Django Channels and Redis channel layer. The seat map on the event detail page updates live as other users lock or book seats.

### Async Notifications
All notifications (email, SMS, WhatsApp, in-app) are dispatched via Celery tasks with automatic retry logic (3 retries, 60s delay). Django signals observe booking and payment events and queue tasks without coupling the apps.

### Payment Webhook Idempotency
Razorpay webhooks are deduplicated using a `WebhookEvent` table — each `event_id` is stored on first receipt and subsequent duplicate webhooks are ignored, preventing double-processing.

---

## Notification Channels

| Channel | Provider | Status |
|---|---|---|
| In-App | Django Channels + Redis | ✅ Live |
| Email | SendGrid / AWS SES | 🔲 Stubbed |
| SMS | TBD | 🔲 Stubbed |
| WhatsApp | Meta Cloud API | 🔲 Stubbed |

---

## User Roles

| Role | Access |
|---|---|
| `attendee` | Browse events, book seats, view bookings, notifications |
| `organizer` | All attendee access + organizer dashboard |
| `admin` | Django admin panel — full access |

---

## CI Pipeline

GitHub Actions runs on every push and pull request to `main`:
- Spins up PostgreSQL 16 + Redis 7
- Installs dependencies
- Runs migrations
- Runs pytest suite

---

## License

MIT