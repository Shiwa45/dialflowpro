# DialFlow Pro - Multitenant Auto Dialer Platform

Modern rebuild of Newfies-Dialer with Django 5 + React 18 + FreeSWITCH.

## Phase 1 - Foundation ✅

### What's Built

**Backend Infrastructure:**
- ✅ Django 5.1 project with split settings (base/development/production)
- ✅ Multi-tenancy via django-tenants (schema-per-tenant isolation)
- ✅ JWT authentication setup (djangorestframework-simplejwt)
- ✅ Celery 5 + Redis for async tasks
- ✅ Django Channels 4 for WebSocket support
- ✅ Docker Compose for full dev stack

**Django Apps Created:**
- ✅ `apps.common` - Base models, health check
- ✅ `apps.tenants` - Tenant & Domain models
- ✅ `apps.accounts` - User model (to be completed)
- ✅ `apps.dialer_settings` - Dialer limits (to be completed)

**Docker Stack:**
- PostgreSQL 16
- Redis 7
- Django API (Daphne ASGI)
- Celery Worker
- Celery Beat

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Make (optional but recommended)

### 2. Setup

```bash
# Clone/navigate to project
cd dialflow

# Copy environment file
cp .env.example .env

# Start development stack
make dev
# OR
docker-compose up

# In another terminal, run migrations
make migrate

# Create superuser
make createsuperuser
```

### 3. Access

- **API**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Health Check**: http://localhost:8000/health/
- **API Docs**: http://localhost:8000/api/docs/ (once drf-spectacular is added)

## Project Structure

```
dialflow/
├── backend/
│   ├── config/                 # Django settings & configuration
│   │   ├── settings/
│   │   │   ├── base.py        # Shared settings
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── celery.py          # Celery app
│   │   ├── asgi.py            # ASGI + WebSocket
│   │   ├── wsgi.py
│   │   └── urls.py
│   ├── apps/
│   │   ├── common/            # Base models, utilities
│   │   ├── tenants/           # Multi-tenancy
│   │   ├── accounts/          # Users, auth
│   │   └── dialer_settings/   # Limits, quotas
│   ├── manage.py
│   └── requirements.txt
├── frontend/                   # React app (Phase 1 - next)
├── freeswitch/                 # FS config & Lua (Phase 3)
├── infra/
│   └── docker/
├── docker-compose.yml
├── Makefile
└── README.md
```

## Next Steps (Phase 1 Remaining)

### Accounts App
- [ ] Create Custom User model with roles
- [ ] Serializers for registration/login
- [ ] ViewSets for user CRUD
- [ ] Password reset flow

### DialerSettings App
- [ ] DialerSetting model (all limits fields)
- [ ] Link to Tenant
- [ ] Admin interface
- [ ] REST API

### React Frontend Init
- [ ] Vite + TypeScript setup
- [ ] shadcn/ui components
- [ ] RTK Query + Redux Toolkit
- [ ] Login page
- [ ] API client configuration

### CI/CD
- [ ] GitHub Actions workflow
- [ ] Ruff linting
- [ ] Pytest tests
- [ ] Docker build

## Commands

```bash
make dev              # Start development environment
make stop             # Stop containers
make migrate          # Run migrations
make shell            # Django shell
make test             # Run tests
make logs             # Tail container logs
make clean            # Clean volumes
make createsuperuser  # Create admin user
```

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `SECRET_KEY` - Django secret
- `FREESWITCH_NODES` - FS node configuration (JSON)

## Technology Stack

**Backend:**
- Python 3.12
- Django 5.1
- DRF 3.15
- Celery 5.4
- Channels 4
- django-tenants 3.7
- PostgreSQL 16
- Redis 7

**Frontend (upcoming):**
- React 18
- TypeScript 5
- Vite 5
- Redux Toolkit
- shadcn/ui
- Tailwind CSS

**Telephony (Phase 3):**
- FreeSWITCH 1.10
- greenswitch (ESL)

## Testing

```bash
# Run all tests
make test

# Run specific test file
docker-compose run --rm api pytest apps/tenants/tests/

# With coverage
docker-compose run --rm api pytest --cov=apps --cov-report=html
```

## Contributing


## License

Proprietary - Internal Development
