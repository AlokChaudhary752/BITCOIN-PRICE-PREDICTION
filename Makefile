.PHONY: install train test-ml test-api test-e2e test test-all dev-api dev-web build docker-up docker-down clean

PYTHON = .venv/bin/python
ifeq ($(OS),Windows_NT)
    PYTHON = .venv/Scripts/python.exe
endif

install:
	$(PYTHON) -m pip install -r packages/ml/requirements.txt
	$(PYTHON) -m pip install -r apps/api/requirements.txt
	$(PYTHON) -m pip install -e packages/ml
	cd apps/web && npm install

train:
	$(PYTHON) -m btc_oracle_ml.train

test-ml:
	$(PYTHON) -m pytest packages/ml/tests -v

test-api:
	$(PYTHON) -m pytest apps/api/tests -v

test-e2e:
	$(PYTHON) -m pytest tests/ -v

test: test-ml test-api

test-all: test-ml test-api test-e2e

dev-api:
	$(PYTHON) -m uvicorn apps.api.src.main:app --host 127.0.0.1 --port 8000 --reload

dev-web:
	cd apps/web && npm run dev

build:
	cd apps/web && npm run build

docker-up:
	docker compose -f infra/docker-compose.yml up --build -d

docker-down:
	docker compose -f infra/docker-compose.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
