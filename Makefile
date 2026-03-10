.PHONY: install dev dev-backend dev-adk dev-frontend deploy-vertex deploy-cloud-run test clean

# Install all dependencies
install:
	pip install -r requirements.txt
	cd frontend && npm install

# Run backend + frontend with Docker
dev:
	docker-compose up --build

# Run backend only (with hot reload)
dev-backend:
	uvicorn server.main:app --reload --port 8000

# Run with ADK's built-in dev UI (no auth, includes web interface)
dev-adk:
	adk web loan_application_agent --port 8000

# Run ADK API server only (no web UI)
dev-api:
	adk api_server loan_application_agent --port 8000

# Run frontend only
dev-frontend:
	cd frontend && npm run dev

# Deploy to Vertex AI Agent Engine
deploy-vertex:
	bash deploy/vertex_deploy.sh

# Deploy to Cloud Run
deploy-cloud-run:
	bash deploy/cloud_run_deploy.sh

# Run tests
test:
	pytest tests/ -v

# Clean build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf frontend/.next frontend/node_modules
