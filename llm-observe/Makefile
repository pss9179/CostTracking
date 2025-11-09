.PHONY: init dev-backend dev-ui test lint format clean

# Initialize project
init:
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -e ".[dev]"
	. venv/bin/activate && cd backend && alembic upgrade head
	@echo "✅ Backend initialized. Run 'make dev-backend' to start."

# Run backend dev server
dev-backend:
	. venv/bin/activate && cd backend && uvicorn llmobserve.api.main:app --reload --host 0.0.0.0 --port 8000

# Run UI dev server (from ui directory)
dev-ui:
	cd ui && pnpm dev

# Run tests
test:
	. venv/bin/activate && pytest --cov=llmobserve --cov-report=term-missing

# Lint
lint:
	. venv/bin/activate && ruff check backend/
	. venv/bin/activate && mypy backend/

# Format
format:
	. venv/bin/activate && black backend/
	. venv/bin/activate && ruff check --fix backend/

# Clean
clean:
	rm -rf venv/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

