.PHONY: help install dev-install migrate run test clean lint format docker-build docker-up docker-down

# Default target
.DEFAULT_GOAL := help

# Help command
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	pip install -r requirements.txt

dev-install: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	npm install

# Database
migrate: ## Run database migrations
	python manage.py migrate

makemigrations: ## Create new migrations
	python manage.py makemigrations

db-reset: ## Reset database (WARNING: destroys all data)
	python manage.py flush --no-input

# Development
run: ## Run development server
	python manage.py runserver

celery-worker: ## Start Celery worker
	celery -A ltcboxoffice worker --loglevel=info

celery-beat: ## Start Celery beat scheduler
	celery -A ltcboxoffice beat --loglevel=info

shell: ## Open Django shell
	python manage.py shell

createsuperuser: ## Create a superuser
	python manage.py createsuperuser

# Testing
test: ## Run tests
	pytest

test-cov: ## Run tests with coverage report
	pytest --cov=. --cov-report=html --cov-report=term

# Code quality
lint: ## Run all linters
	flake8 .
	pylint **/*.py

format: ## Format code with black and isort
	black .
	isort .

format-check: ## Check if code needs formatting
	black --check .
	isort --check-only .

# Static files
collectstatic: ## Collect static files
	python manage.py collectstatic --no-input

# Docker
docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-restart: ## Restart Docker containers
	docker-compose restart

docker-shell: ## Open shell in web container
	docker-compose exec web /bin/bash

# Cleaning
clean: ## Remove Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

clean-all: clean ## Remove all generated files including node_modules
	rm -rf node_modules
	rm -rf staticfiles
	rm -rf .eggs
	rm -rf *.egg-info

# Deployment
deploy-check: ## Check if ready for deployment
	python manage.py check --deploy

loaddata: ## Load initial fixture data
	python manage.py loaddata ltcboxoffice_start_data_fixture.json

# Pre-commit
pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files
