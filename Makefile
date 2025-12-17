COMPOSE := docker compose -f docker-compose.yml

.PHONY: run build build-no-cache rebuild up down stop logs restart

run: build up

restart: stop up

rebuild: down build up

build:
	$(COMPOSE) build

build-no-cache:
	$(COMPOSE) build --no-cache

up:
	$(COMPOSE) up -d

stop:
	$(COMPOSE) stop

down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs -f
