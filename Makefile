.PHONY: help dev stop build migrate shell test

help:
	@echo "DialFlow Pro - Development Commands"
	@echo "===================================="
	@echo "make dev        - Start development environment"
	@echo "make stop       - Stop all containers"
	@echo "make build      - Rebuild containers"
	@echo "make migrate    - Run database migrations"
	@echo "make shell      - Django shell"
	@echo "make test       - Run tests"
	@echo "make logs       - Tail logs"
	@echo "make clean      - Clean database and volumes"

dev:
	docker-compose up

stop:
	docker-compose down

build:
	docker-compose build

migrate:
	docker-compose run --rm api python manage.py migrate_schemas --shared
	docker-compose run --rm api python manage.py migrate

shell:
	docker-compose run --rm api python manage.py shell

test:
	docker-compose run --rm api pytest

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	rm -rf backend/media/* backend/staticfiles/*

# Create superuser
createsuperuser:
	docker-compose run --rm api python manage.py createsuperuser

# Collect static files
collectstatic:
	docker-compose run --rm api python manage.py collectstatic --noinput
