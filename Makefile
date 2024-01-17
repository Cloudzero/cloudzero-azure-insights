# Define variables for Docker image name and container name
IMAGE_NAME := cloudzero-azure-insights-image
CONTAINER_NAME := cloudzero-azure-insights-container

# Default target executed when no arguments are given to make
.PHONY: all
all: build

# Build the Docker image
.PHONY: build
build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME) .

# Transmit Azure Recommendations to CloudZero Insights
.PHONY: run-transmit
run-transmit:
	@echo "Transmitting Azure Recommendations to CloudZero Insights..."
	docker run --rm --name $(CONTAINER_NAME) --env-file .env -it $(IMAGE_NAME) python ./app/app.py --transmit

# Export Azure Recommendations to a CSV file
.PHONY: run-export
run-export:
	@echo "Exporting Azure Recommendations to a CSV file..."
	docker run --rm --name $(CONTAINER_NAME) -v $$(pwd):/usr/src/app/output --env-file .env -it $(IMAGE_NAME) python ./app/app.py --export-csv

# Transmit Azure Recommendations to CloudZero Insights and Export Azure Recommendations to a CSV file
.PHONY: run-both
run-both:
	@echo "Transmitting Azure Recommendations to CloudZero Insights and exporting Azure Recommendations to a CSV file..."
	docker run --rm --name $(CONTAINER_NAME) -v $$(pwd):/usr/src/app/output --env-file .env -it $(IMAGE_NAME) python ./app/app.py --transmit --export-csv

# Remove the Docker container
.PHONY: remove
remove:
	@echo "Removing Docker container..."
	docker rm -f $(CONTAINER_NAME)

# Clean up Docker image
.PHONY: remove clean
clean:
	@echo "Removing Docker image..."
	docker rmi $(IMAGE_NAME)

# View logs of the Docker container
logs:
	@echo "Viewing logs for container $(CONTAINER_ID)"
	@docker logs $(CONTAINER_ID)

# Help
.PHONY: help
help:
	@echo "Makefile commands:"
	@echo "  make build          - Build the Docker image"
	@echo "  make run-transmit   - Transmit Azure Recommendations to CloudZero Insights"
	@echo "  make run-export     - Export Azure Recommendations to a CSV file"
	@echo "  make run-both       - Transmit Azure Recommendations to CloudZero Insights and Export Azure Recommendations to a CSV file"
	@echo "  make remove	     - Remove the Docker container"
	@echo "  make clean          - Remove the Docker image"
	@echo "  make logs           - View the logs of the Docker container"
	@echo "  make help           - Display this help message"
