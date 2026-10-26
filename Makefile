IMAGE ?= expense-tracker-api
CONTAINER ?= expense-tracker
PORT ?= 8000
VENV ?= .venv
PYTHON := $(VENV)/bin/python

# Pass .env to the app only if it exists
ENV_FILE := $(if $(wildcard .env),--env-file .env)

.DEFAULT_GOAL := help
.PHONY: help install run dev test up down logs health docker-build docker-run clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

$(VENV)/bin/activate: requirements.txt requirements-dev.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.txt
	touch $(VENV)/bin/activate

.env:
	cp .env.example .env

install: $(VENV)/bin/activate .env ## Create venv, install dependencies and .env

run: install ## Run locally without --reload
	$(PYTHON) -m uvicorn app_final:app --host 0.0.0.0 --port $(PORT) $(ENV_FILE)

dev: install ## Run locally with --reload
	$(PYTHON) -m uvicorn app_final:app --reload --port $(PORT) $(ENV_FILE)

test: install ## Run tests
	$(PYTHON) -m pytest -v

docker-build: ## Build Docker image
	docker build -t $(IMAGE) .

docker-run: .env ## Run container in background
	docker run -d --name $(CONTAINER) -p $(PORT):8000 $(ENV_FILE) $(IMAGE)

up: docker-build down docker-run ## Build and start app in Docker (one command)
	@echo "App is starting: http://127.0.0.1:$(PORT)/docs"

down: ## Stop and remove container
	-@docker rm -f $(CONTAINER) >/dev/null 2>&1 || true

logs: ## Follow container logs
	docker logs -f $(CONTAINER)

health: ## Check /health and /version
	@curl -sf http://127.0.0.1:$(PORT)/health && echo
	@curl -sf http://127.0.0.1:$(PORT)/version && echo

clean: down ## Remove venv, caches and Docker image
	rm -rf $(VENV) .pytest_cache __pycache__
	-docker rmi $(IMAGE) 2>/dev/null || true
