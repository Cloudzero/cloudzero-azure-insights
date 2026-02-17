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

**Modern CLI with Subcommands**

v2.0 introduces a clean, intuitive CLI powered by Click:

```bash
cz-azure sync --dry-run    # Preview sync
cz-azure export csv        # Export to CSV
cz-azure list --limit 20   # List insights
cz-azure validate          # Check credentials
cz-azure delete            # Clean up insights
```

**Breaking Change: 1:1 Insight Mapping**

Previous versions collapsed multiple Azure recommendations into single CloudZero insights. **v2.0 creates one insight per recommendation** for better tracking and filtering.

**Benefits:**
- Track individual resources (mark specific VMs as addressed)
- Filter by subscription, region, and resource in CloudZero
- More accurate cost attribution per resource
- Clearer insight titles with resource names and SKU changes
- Modern CLI with subcommands for better usability

**Impact:**
- More CloudZero insights created (could be 10K-50K+ for large deployments)
- Use CloudZero's filters and search to manage insights effectively
- First transmission after upgrade will create individual insights for all Azure recommendations

**Migration:** If you have existing collapsed insights, consider cleaning them up before running v2.0. See [CLI Migration Guide](#cli-migration-guide) and [Usage Guide](docs/USAGE.md) for details.

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

### Quick Start Workflow

**1. Validate credentials:**

```bash
make validate
```

**2. Preview what would be synced (dry-run):**

```bash
make dry-run
```

**3. Perform full sync:**

```bash
make run-sync
```

**4. View results:**

```bash
make run-list LIMIT=20
```

### Common Commands

**Sync to CloudZero:**

```bash
make run-sync              # Full sync
make dry-run               # Preview only (recommended first)
make run-sync ARGS='--dry-run'  # Alternative dry-run syntax
```

**Export to CSV:**

```bash
make run-export            # Export to ./output/
```

**List existing insights:**

```bash
make run-list              # Show 10 (default)
make run-list LIMIT=20     # Show 20
make run-list LIMIT=0      # Show all (slow!)
```

**Delete insights:**

```bash
make run-delete            # Interactive deletion with confirmation
```

**Validate credentials:**

```bash
make validate              # Check Azure + CloudZero credentials
```

### Using the CLI Directly

You can also use the CLI directly (without Docker):

```bash
# Install dependencies first
pip install -r requirements.txt

# Source environment variables
source .env  # or: export $(cat .env | xargs)

# Run commands
python -m app.cli validate
python -m app.cli sync --dry-run
python -m app.cli sync
python -m app.cli list --limit 20
python -m app.cli export csv
python -m app.cli delete
```

### CLI Command Reference

```bash
python -m app.cli --help              # Show all commands
python -m app.cli <command> --help    # Help for specific command

Commands:
  sync        Sync Azure recommendations to CloudZero
  export      Export recommendations to file (csv, json)
  list        List existing CloudZero insights
  delete      Delete insights from CloudZero
  validate    Validate Azure and CloudZero credentials
```

> **Note:** First run may take 60-120 minutes for deployments with 10K+ existing CloudZero insights. This is normal and expected. Recommend scheduling overnight. See [Deployment Guide](docs/DEPLOYMENT.md) for scheduling examples.

## CLI Migration Guide

**Upgrading from v1.x?** The flag-based CLI is deprecated but still works with warnings:

| Old Command (v1.x) | New Command (v2.0) |
|--------------------|---------------------|
| `python -m app.app --transmit` | `python -m app.cli sync` |
| `python -m app.app --transmit --dry-run` | `python -m app.cli sync --dry-run` |
| `python -m app.app --export-csv` | `python -m app.cli export csv` |
| `python -m app.app --list-insights` | `python -m app.cli list` |
| `python -m app.app --list-insights --limit=20` | `python -m app.cli list --limit 20` |

**Makefile commands** have been updated and work with both versions:
- `make run-sync` (was `make run-transmit`)
- `make run-export` (unchanged)
- `make run-list` (new, replaces complex args)
- `make dry-run` (new convenience target)
- `make validate` (new)

**Legacy support:** Old commands show deprecation warnings but continue to work. Support will be removed in v3.0.0.

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