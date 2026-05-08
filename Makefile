APP_NAME ?= $(shell basename $(CURDIR))

# Load .env if it exists (init target creates it)
-include .env

PROJECT  := $(GCP_PROJECT_ID)
REGION   := $(or $(GCP_REGION),us-central1)
FUNCTION := $(APP_NAME)

.PHONY: init login setup deploy dev destroy check-env check-gcloud

## Generate access code + write .env (run once)
init:
	@if [ -f .env ]; then echo ".env already exists — delete it and re-run to reset"; exit 0; fi
	$(eval KEY := $(shell openssl rand -hex 16))
	@printf 'GCP_PROJECT_ID=matan-app-zoo\nGCP_REGION=us-central1\nMASTER_KEY=%s\n' "$(KEY)" > .env
	@echo ""
	@echo "✓ .env created with a random access code."
	@echo ""
	@echo "  Your access code (enter this in the app on first launch):"
	@echo "  $(KEY)"
	@echo ""
	@echo "  Save it somewhere safe — it won't be shown again."
	@echo "  Run: make setup"

check-env:
	@test -n "$(PROJECT)"    || (echo "" && echo "ERROR: GCP_PROJECT_ID not set — run: make init" && echo "" && exit 1)
	@test -n "$(MASTER_KEY)" || (echo "" && echo "ERROR: MASTER_KEY not set — run: make init" && echo "" && exit 1)

check-gcloud:
	@command -v gcloud >/dev/null 2>&1 || { \
		echo ""; \
		echo "ERROR: gcloud is not installed."; \
		echo "  Install via brew:  brew install --cask google-cloud-sdk"; \
		echo ""; \
		exit 1; \
	}
	@gcloud auth application-default print-access-token >/dev/null 2>&1 || { \
		echo ""; \
		echo "ERROR: GCP credentials not found. Run:"; \
		echo ""; \
		echo "  make login"; \
		echo ""; \
		exit 1; \
	}

## Authenticate with GCP (run once per machine)
login:
	gcloud auth login
	gcloud auth application-default login
	@echo ""
	@echo "✓ Authenticated. Run: make setup"

## Provision GCP infrastructure (run once per app)
setup: check-env check-gcloud
	@echo "▶ Setting up [$(APP_NAME)] in project [$(PROJECT)]..."
	cd terraform && terraform init -upgrade
	cd terraform && terraform apply \
		-var="app_name=$(APP_NAME)" \
		-var="project_id=$(PROJECT)" \
		-var="region=$(REGION)"
	@echo ""
	@echo "✓ Infrastructure ready. Run: make deploy"

## Deploy the Cloud Function
deploy: check-env
	@echo "▶ Deploying Cloud Function [$(FUNCTION)]..."
	$(eval BUCKET := $(shell cd terraform && terraform output -raw bucket_name 2>/dev/null))
	$(eval SA     := $(shell cd terraform && terraform output -raw sa_email     2>/dev/null))
	@test -n "$(BUCKET)" || (echo "ERROR: Run 'make setup' first" && exit 1)
	gcloud functions deploy $(FUNCTION) \
		--gen2 \
		--runtime=python312 \
		--region=$(REGION) \
		--source=backend/ \
		--entry-point=handler \
		--trigger-http \
		--allow-unauthenticated \
		--service-account=$(SA) \
		--set-env-vars="BUCKET_NAME=$(BUCKET),APP_NAME=$(APP_NAME),MASTER_KEY=$(MASTER_KEY)" \
		--project=$(PROJECT)
	@echo ""
	@echo "✓ Function deployed:"
	@cd terraform && terraform output -raw function_url
	@echo ""

## Start Expo dev server
dev: check-env
	$(eval FURL := $(shell cd terraform && terraform output -raw function_url 2>/dev/null || echo "http://localhost:8080"))
	@printf 'EXPO_PUBLIC_API_URL=%s\nEXPO_PUBLIC_MASTER_KEY=%s\n' "$(FURL)" "$(MASTER_KEY)" > frontend/.env.local
	cd frontend && npm install --silent && npx expo start --tunnel --port 19006 --clear

## Tear down ALL infrastructure for this app (irreversible)
destroy: check-env
	@echo "⚠️  This will DELETE all [$(APP_NAME)] GCP resources and data!"
	@printf "Type the app name to confirm: " && read confirm && [ "$$confirm" = "$(APP_NAME)" ] || (echo "Aborted." && exit 1)
	cd terraform && terraform destroy \
		-var="app_name=$(APP_NAME)" \
		-var="project_id=$(PROJECT)" \
		-var="region=$(REGION)"
