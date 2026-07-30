# Detects the operating system: this conditional ensures cross-platform compatibility
# by adjusting commands for Windows (no sudo, modern Docker CLI syntax) and Linux/macOS.
ifeq ($(OS),Windows_NT)
    SUDO :=
    DOCKER_COMPOSE := docker compose
else
    SUDO := sudo
    DOCKER_COMPOSE := sudo docker-compose
endif

.PHONY: scrap up down

scrap:
	$(SUDO) docker exec django_app python3 manage.py shell -c "from app.tasks import scrap_home_page; scrap_home_page.delay()"
	$(SUDO) docker logs celery_worker -f

up:
	$(DOCKER_COMPOSE) up -d --build

down:
	$(DOCKER_COMPOSE) down -v