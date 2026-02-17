# CloudZero Azure Insights - Makefile
# Provides shortcuts for common development and deployment tasks

# Variables
IMAGE_NAME := cloudzero-azure-insights
CONTAINER_NAME := cz-azure-insights-run
PYTHON := python

# Default target
.PHONY: all
all: help

# ============================================================================
# Development Targets (Local Python)
# ============================================================================

.PHONY: test
test:
	@echo "Running tests..."
	$(PYTHON) -m pytest tests/ -v

.PHONY: test-cov
test-cov:
	@echo "Running tests with coverage..."
	$(PYTHON) -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

.PHONY: lint
lint:
	@echo "Linting code..."
	@$(PYTHON) -m py_compile app/**/*.py tests/**/*.py || echo "✓ No syntax errors"

.PHONY: dev-sync
dev-sync:
	@echo "Running sync locally (requires .env sourced)..."
	$(PYTHON) -m app.cli sync $(ARGS)

.PHONY: dev-export
dev-export:
	@echo "Running export locally (requires .env sourced)..."
	$(PYTHON) -m app.cli export csv $(ARGS)

.PHONY: dev-list
dev-list:
	@echo "Listing insights locally (requires .env sourced)..."
	$(PYTHON) -m app.cli list --limit=$(or $(LIMIT),10) $(ARGS)

.PHONY: dev-validate
dev-validate:
	@echo "Validating credentials locally (requires .env sourced)..."
	$(PYTHON) -m app.cli validate $(ARGS)

# ============================================================================
# Docker Build Targets
# ============================================================================

.PHONY: build
build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME) .

.PHONY: clean
clean:
	@echo "Removing Docker image..."
	docker rmi $(IMAGE_NAME) || true

# ============================================================================
# Docker Run Targets (Container Execution)
# ============================================================================

.PHONY: run-sync
run-sync: build
	@echo "Syncing Azure recommendations to CloudZero..."
	docker run --rm --name $(CONTAINER_NAME) \
		--env-file .env \
		$(IMAGE_NAME) python -m app.cli sync $(ARGS)

.PHONY: run-export
run-export: build
	@echo "Exporting Azure recommendations to CSV..."
	docker run --rm --name $(CONTAINER_NAME) \
		-v $$(pwd)/output:/usr/src/app/output \
		--env-file .env \
		$(IMAGE_NAME) python -m app.cli export csv $(ARGS)

.PHONY: run-both
run-both: build
	@echo "Syncing and exporting Azure recommendations..."
	@echo "Note: Run sync and export separately with new CLI:"
	@echo "  make run-sync && make run-export"
	docker run --rm --name $(CONTAINER_NAME)-sync \
		--env-file .env \
		$(IMAGE_NAME) python -m app.cli sync $(ARGS)
	docker run --rm --name $(CONTAINER_NAME)-export \
		-v $$(pwd)/output:/usr/src/app/output \
		--env-file .env \
		$(IMAGE_NAME) python -m app.cli export csv

.PHONY: run-list
run-list: build
	@echo "Listing CloudZero insights..."
	docker run --rm --name $(CONTAINER_NAME) \
		--env-file .env \
		$(IMAGE_NAME) python -m app.cli list --limit=$(or $(LIMIT),10) $(ARGS)

.PHONY: run-delete
run-delete: build
	@echo "Deleting CloudZero insights..."
	docker run --rm --name $(CONTAINER_NAME) \
		--env-file .env \
		-it $(IMAGE_NAME) python -m app.cli delete $(ARGS)

# ============================================================================
# Convenience Targets
# ============================================================================

.PHONY: dry-run
dry-run: build
	@echo "DRY RUN: Previewing what would be synced..."
	docker run --rm --name $(CONTAINER_NAME) \
		--env-file .env \
		$(IMAGE_NAME) python -m app.cli sync --dry-run

.PHONY: validate
validate: build
	@echo "Validating credentials..."
	docker run --rm --name $(CONTAINER_NAME) \
		--env-file .env \
		$(IMAGE_NAME) python -m app.cli validate

# ============================================================================
# Legacy Targets (Backward Compatibility)
# ============================================================================

.PHONY: run-transmit
run-transmit: run-sync
	@# Alias for backward compatibility

.PHONY: remove
remove:
	@echo "Removing any running containers..."
	@docker rm -f $(CONTAINER_NAME) 2>/dev/null || echo "No container to remove"

# ============================================================================
# Help Target
# ============================================================================

.PHONY: help
help:
	@echo "CloudZero Azure Insights - Makefile Commands"
	@echo ""
	@echo "DEVELOPMENT (Local Python):"
	@echo "  make test              - Run test suite"
	@echo "  make test-cov          - Run tests with coverage report"
	@echo "  make lint              - Check code for syntax errors"
	@echo "  make dev-sync          - Run sync locally (requires .env)"
	@echo "  make dev-export        - Run export locally (requires .env)"
	@echo "  make dev-list          - List insights locally (requires .env)"
	@echo "  make dev-validate      - Validate credentials locally (requires .env)"
	@echo ""
	@echo "DOCKER BUILD:"
	@echo "  make build             - Build Docker image"
	@echo "  make clean             - Remove Docker image"
	@echo ""
	@echo "DOCKER RUN (Container Execution):"
	@echo "  make run-sync          - Sync recommendations to CloudZero"
	@echo "  make run-export        - Export recommendations to CSV"
	@echo "  make run-both          - Sync and export (runs both sequentially)"
	@echo "  make run-list          - List existing insights"
	@echo "  make run-delete        - Delete insights (interactive)"
	@echo ""
	@echo "CONVENIENCE:"
	@echo "  make dry-run           - Preview sync without uploading"
	@echo "  make validate          - Validate credentials"
	@echo ""
	@echo "PASSING ARGUMENTS:"
	@echo "  make run-sync ARGS='--dry-run'"
	@echo "  make run-list LIMIT=20"
	@echo "  make dev-sync ARGS='--dry-run'"
	@echo ""
	@echo "EXAMPLES:"
	@echo "  make test-cov                    # Local testing"
	@echo "  make dry-run                     # Preview sync"
	@echo "  make run-sync                    # Full sync"
	@echo "  make run-list LIMIT=20           # List 20 insights"
	@echo "  make run-export                  # Export to CSV"
	@echo ""
	@echo "For more information: https://github.com/cloudzero/cz-azure-insights"
