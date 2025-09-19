# CloudZero and Azure Advisor Integration Project

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE-OF-CONDUCT.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/release/cloudzero/cz-azure-insights.svg)](https://github.com/Cloudzero/cz-azure-insights/releases)

This project integrates Azure Advisor with CloudZero, allowing Azure Advisor cost recommendations to be extracted, converted to CloudZero insights, and uploaded to CloudZero effectively.

> **Note:** This application does not operate on a scheduled basis. Each time you execute the application, it retrieves cost recommendations from Azure Advisor and only uploads the ones that are currently not present in CloudZero.

## Table of Contents

Make sure this is updated based on the sections included:

- [CloudZero and Azure Advisor Integration Project](#cloudzero-and-azure-advisor-integration-project)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Setting up Environment Variables](#setting-up-environment-variables)
    - [Building the Docker Image](#building-the-docker-image)
  - [Getting Started](#getting-started)
    - [Running the Container](#running-the-container)
    - [Logging](#logging)
  - [Support + Feedback](#support--feedback)
  - [Vulnerability Reporting](#vulnerability-reporting)
  - [Contribution](#contribution)
  - [Thank You!](#thank-you)
  - [What is CloudZero?](#what-is-cloudzero)
  - [License](#license)

## Installation

### Prerequisites

- Docker
- Azure account with appropriate permissions
- CloudZero account

### Azure Permissions Required

Create an Azure AD application with:
- **Reader** role on target subscriptions
- Required API permissions:
  - `Microsoft.Subscription/subscriptions/read`
  - `Microsoft.Advisor/recommendations/read`

### Setting up Environment Variables

Create a `.env` file in the project root directory and populate it with the following environment variables:

```env
AZURE_CLIENT_ID=your_azure_client_id
AZURE_CLIENT_SECRET=your_azure_client_secret
AZURE_TENANT_ID=your_azure_tenant_id
CLOUDZERO_API_KEY=your_cloudzero_api_key
```

### Building the Docker Image

To build the Docker image, run the following command in the project root directory:

```bash
make build
```

This command builds a Docker image named azure-cloudzero-integration based on the Dockerfile in your project.

## Getting Started

### Running the Container

To transmit Azure recommendations to CloudZero Insights, use the following command:

```bash
make run-transmit
```

To export Azure recommendations to a CSV file, use the following command:

```bash
make run-export
```

To do both, use the following command:

```bash
make run-both
```

This command starts a container instance of azure-cloudzero-integration, using the environment variables defined in the .env file.

### Logging

The application logs are configured to provide detailed information about the process and any errors that occur. Check the container logs for debugging and monitoring the application:

```bash
make logs CONTAINER_ID=<container_id>
```

Replace <container_id> with the actual ID of your running container.

## Support + Feedback

- Use Github Issues for code-level support
- Contact support@cloudzero.com for usage, questions, specific cases
- Link to other support forums and FAQs

## Vulnerability Reporting

Please do not report security vulnerabilities on the public GitHub issue tracker. Email [security@cloudzero.com](mailto:security@cloudzero.com) instead.


## Contribution

We appreciate feedback and contribution to this template! Before you get started, please see the following:

- [CloudZero's general contribution guidelines](GENERAL-CONTRIBUTING.md)
- [CloudZero's code of conduct guidelines](CODE-OF-CONDUCT.md)

## Thank You!

A big thank you to all of our sources of inspiration!

- [First Contributions by @Roshanjossey](https://github.com/Roshanjossey/first-contributions)
- [First Timers Only](https://www.firsttimersonly.com/)
- [Sane Github Labels](https://medium.com/@dave_lunny/sane-github-labels-c5d2e6004b63)
- [Awesome README by @matiassingers](https://github.com/matiassingers/awesome-readme)
- [Auth0](https://github.com/auth0/open-source-template) for pulling all this together!

... and many more!

## What is CloudZero?

CloudZero is the only cloud cost intelligence platform that puts engineering in control by connecting technical decisions to business results.:

- [Cost Allocation And Tagging](https://www.cloudzero.com/tour/allocation) Organize and allocate cloud spend in new ways, increase tagging coverage, or work on showback.
- [Kubernetes Cost Visibility](https://www.cloudzero.com/tour/kubernetes) Understand your Kubernetes spend alongside total spend across containerized and non-containerized environments.
- [FinOps And Financial Reporting](https://www.cloudzero.com/tour/finops) Operationalize reporting on metrics such as cost per customer, COGS, gross margin. Forecast spend, reconcile invoices and easily investigate variance.
- [Engineering Accountability](https://www.cloudzero.com/tour/engineering) Foster a cost-conscious culture, where engineers understand spend, proactively consider cost, and get immediate feedback with fewer interruptions and faster and more efficient innovation.
- [Optimization And Reducing Waste](https://www.cloudzero.com/tour/optimization) Focus on immediately reducing spend by understanding where we have waste, inefficiencies, and discounting opportunities.

Learn more about [CloudZero](https://www.cloudzero.com/) on our website [www.cloudzero.com](https://www.cloudzero.com/)

## License

This repo is covered under the [Apache 2.0](LICENSE).