.PHONY: install dev test lint build docker-up help

help:
	@echo "Targets: install, dev, test, lint, build, docker-up"

install:
	poetry install
	pnpm install

dev:
	pnpm exec concurrently -k -n api,web \
		"poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload" \
		"pnpm --filter @amca/web dev"

test:
	poetry run pytest
	pnpm -r run test --if-present

lint:
	poetry run black --check apps packages
	poetry run isort --check-only apps packages
	poetry run ruff check apps packages
	poetry run mypy apps/api/src packages/shared-types/python packages/ml-core/src
	pnpm --filter @amca/web exec eslint . --max-warnings 0
	pnpm exec prettier --check "apps/web/**/*.{ts,tsx,js,jsx,json,css,md}" "packages/shared-types/src/**/*.{ts,tsx}"

build:
	poetry build
	pnpm -r --if-present run build

docker-up:
	docker compose up --build
