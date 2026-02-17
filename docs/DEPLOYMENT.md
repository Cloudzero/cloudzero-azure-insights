# Deployment Guide

This guide provides patterns and examples for deploying the CloudZero Azure Insights integration.

> **⚠️ Note**: Examples below are patterns, not tested configurations. Adjust for your environment. We welcome PRs with tested examples!

## Table of Contents

- [Quick Start](#quick-start)
- [Deployment Patterns](#deployment-patterns)
  - [Scheduled Containers](#scheduled-containers)
  - [Kubernetes Jobs](#kubernetes-jobs)
  - [Cron Jobs](#cron-jobs)
- [Performance Considerations](#performance-considerations)
- [Troubleshooting](#troubleshooting)

## Quick Start

For one-time or manual execution:

```bash
# Build the image
make build

# Run sync (recommended: use dry-run first)
make dry-run

# If dry-run looks good, run for real
make run-sync
```

## Deployment Patterns

### Recommended: Run on a Schedule

This tool is designed for **periodic execution** (daily or weekly). Benefits:

- ✅ Runs automatically without manual intervention
- ✅ Can run overnight when 1-2 hour execution time doesn't matter
- ✅ Ensures CloudZero insights stay up-to-date with Azure Advisor
- ✅ Simple and reliable

**Common schedule patterns:**
- Daily: Run at 2 AM every day
- Weekly: Run at 2 AM every Sunday
- Twice daily: Run at 2 AM and 2 PM

### Scheduled Containers

**Concept**: Use your cloud provider's container scheduling service.

**Azure Container Instances** - Schedule a container to run periodically:
```bash
# General pattern (adjust for your environment)
az container create \
  --resource-group <your-rg> \
  --name cloudzero-insights \
  --image <your-registry>/cloudzero-insights:latest \
  --restart-policy Never \
  --environment-variables <your-env-vars> \
  --schedule "0 2 * * *"
```

**AWS ECS Scheduled Tasks** - Use EventBridge with ECS tasks:
```yaml
# EventBridge rule pattern
ScheduleExpression: cron(0 2 * * ? *)
Target: ECS Task
```

**GCP Cloud Run Jobs** - Schedule Cloud Run executions:
```bash
# General pattern
gcloud run jobs create cloudzero-insights \
  --image <your-image> \
  --schedule "0 2 * * *"
```

### Kubernetes Jobs

**Concept**: Use Kubernetes CronJob for scheduled execution.

**Key components:**
- CronJob with schedule spec (e.g., `0 2 * * *`)
- Secrets for credentials (never hardcode)
- Resource limits (tool can use significant CPU/memory during 60-120 min run)
- Job history limits for cleanup

**Pattern:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cloudzero-insights
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
          - name: insights
            image: <your-image>
            command: ["python", "-m", "app.cli", "sync"]
            envFrom:
            - secretRef:
                name: cloudzero-azure-credentials
```

**Monitoring:**
- Check CronJob status: `kubectl get cronjobs`
- View job history: `kubectl get jobs`
- View logs: `kubectl logs job/<job-name>`

### Cron Jobs

**Concept**: Traditional cron on a VM running Docker.

**Pattern:**
```bash
# Wrapper script (run-insights.sh)
#!/bin/bash
docker run --rm --env-file /path/to/.env <your-image> python -m app.cli sync

# Crontab entry
0 2 * * * /path/to/run-insights.sh >> /var/log/cz-insights.log 2>&1
```

**Best practices:**
- Use absolute paths in cron
- Redirect output to log file
- Set proper permissions on .env file
- Consider using `flock` to prevent overlapping runs

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
1. **All recommendations already exist**: Check with `make run-list LIMIT=10`
2. **Dry-run mode**: Ensure you're not using `--dry-run` flag
3. **API errors**: Check logs for CloudZero API errors

**Debug**:
```bash
# Run with dry-run to see what would be uploaded
make dry-run

# Check existing insights
make run-list LIMIT=20
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
