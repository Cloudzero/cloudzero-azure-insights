# Deployment Guide

This guide provides examples for deploying the CloudZero Azure Insights integration in various environments.

## Table of Contents

- [Quick Start](#quick-start)
- [Scheduled Execution](#scheduled-execution)
  - [Azure Container Instances](#azure-container-instances)
  - [Kubernetes CronJob](#kubernetes-cronjob)
  - [Docker with Cron](#docker-with-cron)
  - [GitHub Actions](#github-actions)
- [Performance Considerations](#performance-considerations)
- [Troubleshooting](#troubleshooting)

## Quick Start

For one-time or manual execution:

```bash
# Build the image
make build

# Run transmission (recommended: use dry-run first)
make run-transmit ARGS="--dry-run"

# If dry-run looks good, run for real
make run-transmit
```

## Scheduled Execution

### Recommended: Run on a Schedule

This tool is designed for **periodic execution** (daily or weekly). Benefits:

- ✅ Runs automatically without manual intervention
- ✅ Can run overnight when 1-2 hour execution time doesn't matter
- ✅ Ensures CloudZero insights stay up-to-date with Azure Advisor
- ✅ Simple and reliable

### Azure Container Instances

**Best for**: Azure-native deployments

Create a scheduled container instance:

```bash
az container create \
  --resource-group myResourceGroup \
  --name cloudzero-azure-insights \
  --image cloudzero/azure-insights:latest \
  --restart-policy Never \
  --command-line "python ./app/app.py --transmit" \
  --environment-variables \
    AZURE_CLIENT_ID=$AZURE_CLIENT_ID \
    AZURE_CLIENT_SECRET=$AZURE_CLIENT_SECRET \
    AZURE_TENANT_ID=$AZURE_TENANT_ID \
    CLOUDZERO_API_KEY=$CLOUDZERO_API_KEY \
  --schedule "0 2 * * *"  # 2 AM daily
```

**Schedule options:**
- Daily: `"0 2 * * *"` (2 AM every day)
- Weekly: `"0 2 * * 0"` (2 AM every Sunday)
- Twice daily: `"0 2,14 * * *"` (2 AM and 2 PM)

### Kubernetes CronJob

**Best for**: Kubernetes environments

Create `cloudzero-insights-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cloudzero-azure-insights
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
          - name: insights
            image: cloudzero/azure-insights:latest
            command: ["python", "./app/app.py", "--transmit"]
            env:
            - name: AZURE_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: azure-credentials
                  key: client-id
            - name: AZURE_CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: azure-credentials
                  key: client-secret
            - name: AZURE_TENANT_ID
              valueFrom:
                secretKeyRef:
                  name: azure-credentials
                  key: tenant-id
            - name: CLOUDZERO_API_KEY
              valueFrom:
                secretKeyRef:
                  name: cloudzero-credentials
                  key: api-key
```

Create secrets:

```bash
# Azure credentials
kubectl create secret generic azure-credentials \
  --from-literal=client-id=$AZURE_CLIENT_ID \
  --from-literal=client-secret=$AZURE_CLIENT_SECRET \
  --from-literal=tenant-id=$AZURE_TENANT_ID

# CloudZero credentials
kubectl create secret generic cloudzero-credentials \
  --from-literal=api-key=$CLOUDZERO_API_KEY
```

Deploy:

```bash
kubectl apply -f cloudzero-insights-cronjob.yaml
```

Monitor:

```bash
# View CronJob status
kubectl get cronjobs

# View recent job runs
kubectl get jobs --selector=job-name=cloudzero-azure-insights

# View logs from latest run
kubectl logs -l job-name=cloudzero-azure-insights --tail=100
```

### Docker with Cron

**Best for**: VM or on-premise deployments

Create a cron wrapper script `run-insights.sh`:

```bash
#!/bin/bash
set -e

# Load environment variables
source /path/to/.env

# Run container
docker run --rm \
  --env-file /path/to/.env \
  cloudzero/azure-insights:latest \
  python ./app/app.py --transmit

# Log completion
echo "$(date): CloudZero insights sync completed" >> /var/log/cz-insights.log
```

Make it executable:

```bash
chmod +x run-insights.sh
```

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add line for daily execution at 2 AM
0 2 * * * /path/to/run-insights.sh 2>&1 | logger -t cloudzero-insights
```

### GitHub Actions

**Best for**: GitOps workflows

Create `.github/workflows/sync-azure-insights.yml`:

```yaml
name: Sync Azure Insights to CloudZero

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
  workflow_dispatch:  # Allow manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t cloudzero-insights .

      - name: Run insights sync
        env:
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          CLOUDZERO_API_KEY: ${{ secrets.CLOUDZERO_API_KEY }}
        run: |
          docker run --rm \
            -e AZURE_CLIENT_ID \
            -e AZURE_CLIENT_SECRET \
            -e AZURE_TENANT_ID \
            -e CLOUDZERO_API_KEY \
            cloudzero-insights \
            python ./app/app.py --transmit

      - name: Log completion
        run: echo "CloudZero insights sync completed at $(date)"
```

Configure secrets in GitHub repository settings.

## Performance Considerations

### Execution Time

Expected execution times based on deployment size:

| Azure Insights | CloudZero Insights | Fetch Time | Total Time |
|----------------|-------------------|------------|------------|
| 100 | 1,000 | 1-2 min | 2-3 min |
| 1,000 | 10,000 | 10-15 min | 15-20 min |
| 10,000 | 50,000 | 60-90 min | 70-100 min |

**Key insight**: Execution time scales with the number of existing CloudZero insights, not Azure recommendations.

### First Run vs. Subsequent Runs

- **First run**: Fetches all existing CloudZero insights for duplicate checking (slow)
- **Subsequent runs**: Same fetch time (checks all insights each time)
- **New recommendations**: Only new Azure recommendations are uploaded

### Optimization Tips

1. **Schedule overnight**: Run during off-hours when execution time doesn't matter
2. **Monitor logs**: Check for errors or API issues in scheduled runs
3. **Dry-run testing**: Use `--dry-run` flag to preview before real execution
4. **Start small**: Test with a single subscription before scaling

## Troubleshooting

### Long Execution Times

**Symptom**: Tool runs for 1-2 hours

**Cause**: Large number of existing CloudZero insights (50K+)

**Solution**: This is expected behavior. The tool must fetch all insights to check for duplicates.

**Mitigation**:
- Schedule during off-hours (overnight)
- Run less frequently if insights don't change often (weekly instead of daily)

### Authentication Failures

**Symptom**: `AADSTS7000222: The provided client secret keys are expired`

**Solution**:
1. Create new Azure AD app credentials in Azure Portal
2. Update `AZURE_CLIENT_SECRET` environment variable
3. Ensure credentials have **Reader** role on subscriptions

### No Insights Created

**Symptom**: Tool completes but no new insights appear in CloudZero

**Possible causes**:
1. **All recommendations already exist**: Check with `--list-insights --limit=10`
2. **Dry-run mode**: Ensure you're not using `--dry-run` flag
3. **API errors**: Check logs for CloudZero API errors

**Debug**:
```bash
# Run with dry-run to see what would be uploaded
make run-transmit ARGS="--dry-run"

# Check existing insights
make run-transmit ARGS="--list-insights --limit=20"
```

### Container Scheduling Issues

**Kubernetes**: Check CronJob status
```bash
kubectl describe cronjob cloudzero-azure-insights
kubectl get jobs --selector=job-name=cloudzero-azure-insights
```

**Azure Container Instances**: Check container logs
```bash
az container logs --resource-group myResourceGroup --name cloudzero-azure-insights
```

### Rate Limiting

**Symptom**: `429 Too Many Requests` errors

**Solution**:
- CloudZero API has rate limits
- Reduce execution frequency (daily instead of hourly)
- Contact CloudZero support if limits are too restrictive

## Best Practices

1. **Use secrets management**: Store credentials in Azure Key Vault, K8s Secrets, or AWS Secrets Manager
2. **Monitor scheduled runs**: Set up alerting for failed executions
3. **Test in non-prod first**: Verify with dry-run and small Azure subscriptions
4. **Keep Docker image updated**: Pull latest image regularly for bug fixes
5. **Review logs regularly**: Check for warnings or errors in scheduled runs
6. **Document your schedule**: Record when and how often the tool runs for your team

## Support

For issues or questions:
- GitHub Issues: https://github.com/cloudzero/cz-azure-insights/issues
- CloudZero Support: support@cloudzero.com
