# Usage Guide

This guide explains how to use the CloudZero Azure Insights integration tool.

## Table of Contents

- [Overview](#overview)
- [Commands](#commands)
  - [Transmit to CloudZero](#transmit-to-cloudzero)
  - [Export to CSV](#export-to-csv)
  - [List Insights](#list-insights)
- [Use Cases](#use-cases)
- [Understanding the Output](#understanding-the-output)
- [Best Practices](#best-practices)

## Overview

This tool bridges the gap between Azure Advisor and CloudZero by:
1. Fetching cost optimization recommendations from Azure Advisor
2. Checking for duplicates in CloudZero
3. Creating CloudZero insights for new recommendations

**Key features:**
- ✅ **1:1 mapping**: One CloudZero insight per Azure recommendation
- ✅ **Duplicate prevention**: Automatically skips existing recommendations
- ✅ **Enhanced metadata**: Uses Azure categories, effort levels, and detailed descriptions
- ✅ **Dry-run mode**: Preview changes before applying

## Commands

### Transmit to CloudZero

Upload Azure Advisor recommendations to CloudZero as insights.

#### Dry Run (Preview)

**Always run dry-run first** to preview what will be uploaded:

```bash
make run-transmit ARGS="--dry-run"
```

**Output:**
```
[DRY RUN] Would upload:
  Title: Right-size VM: vm-firewall-prod (D8ls_v5 → B8als_v2)
  Cost Impact: $708
  Category: cost | Effort: medium
```

#### Live Transmission

After verifying dry-run output:

```bash
make run-transmit
```

**Expected behavior:**
1. Fetches all subscriptions from Azure
2. Fetches Azure Advisor recommendations for each subscription
3. Fetches existing CloudZero insights (can take 60-120 min for large deployments)
4. Filters out duplicates
5. Uploads new recommendations as CloudZero insights

**Output:**
```
INFO - Fetching Azure subscription IDs...
INFO - Fetching Azure Advisor cost recommendations...
INFO - Fetching existing CloudZero Azure insights...
INFO - Page 1: Retrieved 100 insights (total so far: 100/50000)
...
INFO - Processing 42 recommendations individually...
INFO - Insight transmitted: Right-size VM: vm-firewall-prod (D8ls_v5 → B8als_v2)
INFO - Insights transmitted to CloudZero: 42/42
```

### Export to CSV

Export Azure Advisor recommendations to a local CSV file (without uploading to CloudZero).

```bash
make run-export
```

**Output:**
- Creates `azure_insights_<timestamp>.csv` in the current directory
- Includes: title, category, impact, cost savings, subscription, resource details

**Use cases:**
- Auditing Azure recommendations
- Reporting to stakeholders
- Offline analysis
- Comparing recommendations over time

### List Insights

View existing CloudZero insights that were created from Azure Advisor.

#### Quick Preview (First 10)

```bash
make run-transmit ARGS="--list-insights"
```

**Output:**
```
✓ Displaying 10 of 50000+ insights:

1. Right-size VM: vm-firewall-prod (D8ls_v5 → B8als_v2)
   Status: new | Cost Impact: $708 | Source: Azure Advisor
   Created: 1751453753 | Updated: 1751453753
2. Shutdown VM: vm-test-dev
   Status: new | Cost Impact: $150 | Source: Azure Advisor
   Created: 1751453754 | Updated: 1751453754
...
```

#### Custom Limit

```bash
make run-transmit ARGS="--list-insights --limit=50"
```

#### All Insights (Warning: Slow)

```bash
make run-transmit ARGS="--list-insights --limit=0"
```

**Note**: For large deployments (50K+ insights), this can take 60-120 minutes. You'll be prompted to confirm.

## Use Cases

### Use Case 1: Initial Setup

**Scenario**: First time running the tool

**Steps:**
```bash
# 1. Preview what would be uploaded
make run-transmit ARGS="--dry-run"

# 2. Review output carefully
# 3. If everything looks good, run for real
make run-transmit

# 4. Verify insights appear in CloudZero UI
```

**Expected first run:**
- Takes 60-120 minutes for large Azure deployments
- Uploads all Azure Advisor recommendations (could be 100-10,000+)
- Creates individual CloudZero insight for each recommendation

### Use Case 2: Daily Scheduled Sync

**Scenario**: Keep CloudZero updated with latest Azure recommendations

**Setup:**
```bash
# Schedule to run daily at 2 AM
# See DEPLOYMENT.md for scheduling examples
```

**Expected behavior:**
- Fetches current Azure recommendations
- Skips recommendations already in CloudZero
- Only uploads new recommendations (typically 0-50 per day)
- Completes in 60-90 minutes

### Use Case 3: Auditing and Reporting

**Scenario**: Export recommendations for offline analysis

**Steps:**
```bash
# Export to CSV
make run-export

# Analyze locally
open azure_insights_*.csv
```

**Use this for:**
- Monthly cost optimization reports
- Tracking recommendation trends
- Sharing with finance team
- Comparing with previous exports

### Use Case 4: Testing and Debugging

**Scenario**: Verify tool configuration without affecting production

**Steps:**
```bash
# 1. Use dry-run to test Azure connectivity
make run-transmit ARGS="--dry-run"

# 2. Check a small sample of existing insights
make run-transmit ARGS="--list-insights --limit=5"

# 3. Verify credentials work
# If dry-run shows recommendations, credentials are correct
```

## Understanding the Output

### Insight Mapping

Each Azure Advisor recommendation becomes a CloudZero insight with:

**Title Format:**
- SKU change: `Right-size VM: vm-name (CurrentSKU → TargetSKU)`
- Shutdown: `Shutdown vm-name`
- Other: `Recommendation: resource-name`

**Fields:**
- **Category**: From Azure (cost, performance, security, etc.)
- **Effort**: From Azure impact level (high, medium, low)
- **Cost Impact**: Annual savings amount
- **Status**: Always "new" on creation
- **Source**: "Azure Advisor"

**Description includes:**
- Subscription ID and region
- Current and recommended SKU
- Savings (monthly and annual)
- Carbon savings
- Utilization metrics (CPU, memory, network)
- Azure Advisor recommendation ID

### Understanding Counts

**Log output breakdown:**
```
INFO - Fetching Azure Advisor cost recommendations...
     → Number of recommendations from Azure

INFO - Filtering Azure Advisor recommendations...
INFO - Remaining recommendations: 42
     → After removing duplicates (already in CloudZero)

INFO - Processing 42 recommendations individually...
     → Creating insights for new recommendations

INFO - Insights transmitted to CloudZero: 42/42
     → Success count / Total attempted
```

### Duplicate Detection

The tool prevents duplicates by:
1. Fetching all existing CloudZero insights with source "Azure Advisor"
2. Extracting Azure Advisor recommendation IDs from insight descriptions
3. Filtering out Azure recommendations that already exist

**Why this matters:**
- Running the tool multiple times won't create duplicates
- Safe to run on a schedule
- Can re-run after failures without issues

## Best Practices

### 1. Always Use Dry-Run First

```bash
# Before first run
make run-transmit ARGS="--dry-run"

# Before scheduled deployment
make run-transmit ARGS="--dry-run"

# After configuration changes
make run-transmit ARGS="--dry-run"
```

### 2. Schedule for Off-Hours

The tool can take 60-120 minutes for large deployments. Schedule it when:
- ✅ Overnight (2-4 AM)
- ✅ Weekends
- ✅ Low-activity periods
- ❌ Not during business hours

### 3. Monitor Scheduled Runs

Set up monitoring for:
- ✅ Job completion status
- ✅ Error logs
- ✅ Number of insights uploaded
- ✅ Execution duration trends

### 4. Review New Insights Regularly

After scheduled runs, check:
- CloudZero UI for new insights
- Ensure insights are actionable
- Mark addressed insights as complete
- Ignore irrelevant recommendations

### 5. Test with Subset First

For initial deployment:
```bash
# Option 1: Test with single subscription
# (modify .env to use one subscription)

# Option 2: Use dry-run extensively
make run-transmit ARGS="--dry-run"
```

### 6. Keep Credentials Secure

- ✅ Use environment variables (not hardcoded)
- ✅ Use secrets management (Azure Key Vault, K8s Secrets)
- ✅ Rotate credentials regularly
- ✅ Use minimal required permissions (Reader role)
- ❌ Don't commit credentials to git
- ❌ Don't log credentials

### 7. Document Your Usage

Create a runbook for your team:
- How often the tool runs
- Where it's deployed
- Who to contact for issues
- How to review results in CloudZero

## Troubleshooting

### No New Insights Created

**Check:**
1. Are there actually new Azure recommendations?
   ```bash
   make run-transmit ARGS="--dry-run"
   ```
2. Were they already uploaded previously?
   ```bash
   make run-transmit ARGS="--list-insights --limit=20"
   ```

### Slow Execution

**Expected**: 60-120 minutes for deployments with 10K-50K existing insights

**Not an issue**: This is normal behavior. Schedule overnight.

### Authentication Errors

**Fix:**
1. Verify credentials in `.env` file
2. Check Azure AD app has Reader role
3. Ensure credentials haven't expired
4. Test with dry-run

## Support

- **GitHub Issues**: https://github.com/cloudzero/cz-azure-insights/issues
- **CloudZero Support**: support@cloudzero.com
- **Documentation**: See main README.md
