.PHONY: dev-api dev-web seed install-api install-sdk install-web install help

help:
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies (API, SDK, Web)"
	@echo "  make install-api  - Install collector API dependencies"
	@echo "  make install-sdk  - Install SDK in editable mode"
	@echo "  make install-web  - Install web dependencies"
	@echo "  make dev-api      - Start FastAPI collector on :8000"
	@echo "  make dev-web      - Start Next.js dashboard on :3000"
	@echo "  make seed         - Run test script to generate sample data"

install: install-api install-sdk install-web

install-api:
	cd collector && pip install -e .

install-sdk:
	cd sdk/python && pip install -e .

install-web:
	cd web && pnpm install

dev-api:
	cd collector && uvicorn main:app --reload --port 8000

dev-web:
	cd web && pnpm dev

seed:
	python scripts/test_run.py

