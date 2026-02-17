# CloudZero and Azure Advisor Integration Project

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE-OF-CONDUCT.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/release/cloudzero/cz-azure-insights.svg)](https://github.com/Cloudzero/cz-azure-insights/releases)

This project integrates Azure Advisor with CloudZero, allowing Azure Advisor cost recommendations to be extracted, converted to CloudZero insights, and uploaded to CloudZero effectively.

## Key Features

- ✅ **1:1 Mapping**: Creates one CloudZero insight per Azure Advisor recommendation for better tracking
- ✅ **Duplicate Prevention**: Automatically skips recommendations already in CloudZero
- ✅ **Enhanced Metadata**: Uses Azure categories, effort levels, and detailed resource information
- ✅ **Scheduled Execution**: Designed to run periodically (daily/weekly) via container scheduling
- ✅ **Multiple Export Options**: Upload to CloudZero, export to CSV, or both

## Why This Tool Exists

CloudZero automatically imports cost recommendations from:
- ✅ AWS Trusted Advisor
- ✅ GCP Recommender
- ❌ Azure Advisor (not supported)

**This tool bridges that gap** by syncing Azure Advisor recommendations to CloudZero as insights.

## Quick Links

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Scheduling examples (Azure Container Instances, K8s, cron)
- **[Usage Guide](docs/USAGE.md)** - Commands, use cases, and best practices
- **[Azure Permissions](docs/DEPLOYMENT.md#azure-permissions-required)** - Required Azure AD setup

> **Recommended Usage:** Schedule this tool to run daily during off-hours (2-4 AM). First run may take 60-120 minutes for large deployments, but ensures your CloudZero insights stay synchronized with Azure Advisor recommendations.

## What's New in v2.0

**Breaking Change: 1:1 Insight Mapping**

Previous versions collapsed multiple Azure recommendations into single CloudZero insights. **v2.0 creates one insight per recommendation** for better tracking and filtering.

**Benefits:**
- Track individual resources (mark specific VMs as addressed)
- Filter by subscription, region, and resource in CloudZero
- More accurate cost attribution per resource
- Clearer insight titles with resource names and SKU changes

**Impact:**
- More CloudZero insights created (could be 10K-50K+ for large deployments)
- Use CloudZero's filters and search to manage insights effectively
- First transmission after upgrade will create individual insights for all Azure recommendations

**Migration:** If you have existing collapsed insights, consider cleaning them up before running v2.0. See [Usage Guide](docs/USAGE.md) for details.

## Table of Contents

- [Key Features](#key-features)
- [Why This Tool Exists](#why-this-tool-exists)
- [Quick Links](#quick-links)
- [What's New in v2.0](#whats-new-in-v20)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Azure Permissions Required](#azure-permissions-required)
  - [Setting up Environment Variables](#setting-up-environment-variables)
  - [Building the Docker Image](#building-the-docker-image)
- [Getting Started](#getting-started)
  - [Running the Container](#running-the-container)
  - [Logging](#logging)
- [Documentation](#documentation)
- [Support + Feedback](#support--feedback)
- [Vulnerability Reporting](#vulnerability-reporting)
- [Contribution](#contribution)
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

**⚠️ Always use dry-run first:**

```bash
make run-transmit ARGS="--dry-run"
```

This previews what would be uploaded without actually creating insights.

**Transmit to CloudZero:**

```bash
make run-transmit
```

**Export to CSV:**

```bash
make run-export
```

**Both:**

```bash
make run-both
```

**List existing insights:**

```bash
make run-transmit ARGS="--list-insights --limit=20"
```

> **Note:** First run may take 60-120 minutes for deployments with 10K+ existing CloudZero insights. This is normal and expected. Recommend scheduling overnight. See [Deployment Guide](docs/DEPLOYMENT.md) for scheduling examples.

### Logging

The application logs are configured to provide detailed information about the process and any errors that occur. Check the container logs for debugging and monitoring the application:

```bash
make logs CONTAINER_ID=<container_id>
```

Replace <container_id> with the actual ID of your running container.

## Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Scheduling options and examples
  - Azure Container Instances (scheduled)
  - Kubernetes CronJob
  - Docker with cron
  - GitHub Actions

- **[Usage Guide](docs/USAGE.md)** - Commands and best practices
  - Command reference
  - Use cases and workflows
  - Understanding output
  - Troubleshooting

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