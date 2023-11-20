# Azure Advisor and CloudZero Integration Project

This project integrates Azure Advisor with CloudZero, allowing Azure Advisor cost recommendations to be extracted, converted to CloudZero insights, and uploaded to CloudZero effectively.

## Configuration

### Prerequisites

- Docker
- Azure account with appropriate permissions
- CloudZero account

### Setting up Environment Variables

Create a `.env` file in the project root directory and populate it with the following environment variables:

```env
AZURE_CLIENT_ID=your_azure_client_id
AZURE_CLIENT_SECRET=your_azure_client_secret
AZURE_TENANT_ID=your_azure_tenant_id
CLOUDZERO_API_KEY=your_cloudzero_api_key
```

## Building the Docker Image

To build the Docker image, run the following command in the project root directory:

```bash
docker build -t azure-cloudzero-integration .
```

This command builds a Docker image named azure-cloudzero-integration based on the Dockerfile in your project.

## Running the Container

To run the container, use the following command:

```bash
docker run --env-file .env azure-cloudzero-integration
```

This command starts a container instance of azure-cloudzero-integration, using the environment variables defined in the .env file.

## Logging

The application logs are configured to provide detailed information about the process and any errors that occur. Check the container logs for debugging and monitoring the application:

```bash
docker logs [container_id]
```

Replace [container_id] with the actual ID of your running container.