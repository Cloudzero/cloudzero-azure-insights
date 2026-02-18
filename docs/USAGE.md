# Usage Guide

This guide explains how to use the CloudZero Azure Insights integration tool with the v2.0 CLI.

## Table of Contents

- [Overview](#overview)
- [CLI Quick Reference](#cli-quick-reference)
- [Commands](#commands)
  - [Validate Credentials](#validate-credentials)
  - [Sync to CloudZero](#sync-to-cloudzero)
  - [Export to CSV](#export-to-csv)
  - [List Insights](#list-insights)
  - [Delete Insights](#delete-insights)
- [Use Cases](#use-cases)
- [Understanding the Output](#understanding-the-output)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

This tool bridges the gap between Azure Advisor and CloudZero by:
1. Fetching cost optimization recommendations from Azure Advisor
2. Checking for duplicates in CloudZero
3. Creating CloudZero insights for new recommendations (1:1 mapping)

**Key features:**
- ✅ **Modern CLI**: Intuitive subcommand structure with excellent help text
- ✅ **1:1 mapping**: One CloudZero insight per Azure recommendation
- ✅ **Duplicate prevention**: Automatically skips existing recommendations
- ✅ **Enhanced metadata**: Uses Azure categories, effort levels, and detailed descriptions
- ✅ **Dry-run mode**: Preview changes before applying
- ✅ **Colored output**: Clear visual feedback
- ✅ **Progress tracking**: Progress bars for long-running operations

## CLI Quick Reference

```bash
# Using Makefile (Docker)
make validate                # Check credentials
make dry-run                 # Preview sync
make run-sync                # Full sync
make run-export              # Export to CSV
make run-list LIMIT=20       # List 20 insights
make run-delete              # Delete insights (interactive)

# Using CLI directly (local Python)
python -m app.cli validate               # Check credentials
python -m app.cli sync --dry-run         # Preview sync
python -m app.cli sync                   # Full sync
python -m app.cli export csv             # Export to CSV
python -m app.cli list --limit 20        # List 20 insights
python -m app.cli delete                 # Delete insights
python -m app.cli <command> --help       # Command-specific help
```

## Commands

### Validate Credentials

Check that Azure and CloudZero credentials are configured correctly.

#### Makefile

```bash
# Validate all credentials
make validate

# Using Docker run directly
docker run --rm --env-file .env cloudzero-azure-insights python -m app.cli validate
```

#### CLI Direct

```bash
# Validate all credentials
python -m app.cli validate

# Validate Azure only
python -m app.cli validate --azure

# Validate CloudZero only
python -m app.cli validate --cloudzero
```

#### Output

```
Validating Azure credentials...
✓ Azure: Valid (3 subscription(s) found)
Validating CloudZero credentials...
✓ CloudZero: Valid

✓ All credentials validated successfully
```

**When to use:**
- Before first run
- After updating credentials
- Troubleshooting connectivity issues
- CI/CD pipeline validation

---

### Sync to CloudZero

Upload Azure Advisor recommendations to CloudZero as insights.

#### Dry Run (Preview)

**Always run dry-run first** to preview what will be uploaded:

```bash
# Using Makefile
make dry-run

# Using CLI directly
python -m app.cli sync --dry-run
```

**Output:**
```
🔍 DRY RUN MODE
Previewing what would be uploaded (no actual changes)

Initializing Azure and CloudZero clients...
Fetching Azure subscriptions...
✓ Found 3 subscription(s)
Fetching Azure Advisor recommendations...
✓ Retrieved 156 recommendation(s)
Checking for existing insights in CloudZero...
✓ 42 new recommendation(s) to sync

Syncing recommendations  [####################################]  42/42

✓ [DRY RUN] Would create 42 insight(s)
```

#### Live Sync

After verifying dry-run output:

```bash
# Using Makefile
make run-sync

# Using CLI directly
python -m app.cli sync
```

**Expected behavior:**
1. Fetches all subscriptions from Azure
2. Fetches Azure Advisor recommendations for each subscription
3. Fetches existing CloudZero insights (can take 60-120 min for large deployments)
4. Filters out duplicates by recommendation ID
5. Uploads new recommendations as CloudZero insights with 1:1 mapping
6. Shows progress bar during upload

**Output:**
```
Initializing Azure and CloudZero clients...
Fetching Azure subscriptions...
✓ Found 3 subscription(s)
Fetching Azure Advisor recommendations...
✓ Retrieved 156 recommendation(s)
Checking for existing insights in CloudZero...
✓ 42 new recommendation(s) to sync

⚠️  Using 1:1 mapping: One CloudZero insight per Azure recommendation
⚠️  This will create 42 insights (before duplicate filtering)
⚠️  Run with --dry-run first to preview changes

Syncing recommendations  [####################################]  42/42

✓ Successfully created 42 insight(s)
```

**What gets uploaded:**

Each Azure recommendation becomes one CloudZero insight with:
- **Title**: Specific resource name and SKU change (e.g., "Right-size VM: vm-prod (D8 → B8)")
- **Description**: Detailed markdown with subscription, region, SKU, savings, utilization
- **Cost Impact**: Monthly savings amount
- **Category**: Mapped from Azure (cost, performance, etc.)
- **Effort**: Mapped from Azure impact (high, medium, low)
- **Source**: "Azure Advisor"
- **Status**: "new"

---

### Export to CSV

Export Azure Advisor recommendations to a local CSV file (without uploading to CloudZero).

#### Makefile

```bash
# Export to ./output/azure_advisor_recommendations.csv
make run-export

# Export to custom directory (CLI direct only)
python -m app.cli export csv --output ./reports/
```

#### CLI Direct

```bash
# Export to default location (./output/)
python -m app.cli export csv

# Export to custom directory
python -m app.cli export csv --output ./reports/
```

**Output:**
```
Initializing Azure client...
Fetching Azure subscriptions...
✓ Found 3 subscription(s)
Fetching Azure Advisor recommendations...
✓ Retrieved 156 recommendation(s)
Exporting to CSV in ./output/...
✓ Successfully exported to ./output/azure_advisor_recommendations.csv
```

**CSV includes:**
- Subscription ID
- Recommendation ID
- Resource name
- Current SKU
- Target SKU
- Monthly savings
- Annual savings
- Region
- Impact level
- All extended properties from Azure

**Use cases:**
- Auditing Azure recommendations
- Reporting to stakeholders
- Offline analysis
- Comparing recommendations over time
- Importing into spreadsheet tools

---

### List Insights

View existing CloudZero insights that were created from Azure Advisor with optional filters.

#### Basic Usage

```bash
# List 10 insights (default)
python -m app.cli list

# List 20 insights
python -m app.cli list --limit 20

# List all insights (SLOW - can take hours!)
python -m app.cli list --limit 0
```

#### Filtering Options

All filters can be combined to narrow results:

```bash
# Filter by status
python -m app.cli list --status new
python -m app.cli list --status ignored

# Filter by Azure subscription
python -m app.cli list --subscription sub-abc-123

# Filter by cost impact
python -m app.cli list --min-cost 100          # >= $100
python -m app.cli list --max-cost 50           # <= $50
python -m app.cli list --min-cost 50 --max-cost 500  # Between $50-$500

# Filter by title
python -m app.cli list --title "Right-size"    # Title contains "Right-size"
python -m app.cli list --title "Shutdown"      # Title contains "Shutdown"

# Filter by timestamp (Unix timestamp)
python -m app.cli list --created-after 1705881600   # After Jan 22, 2024
python -m app.cli list --created-before 1708473600  # Before Feb 21, 2024

# Filter by Azure Advisor recommendation ID
python -m app.cli list --rec-id abc-123-def

# Combine multiple filters
python -m app.cli list --status new --min-cost 100 --limit 50
python -m app.cli list --subscription sub-123 --title "VM"
```

#### Available Filters

| Filter | Type | Description |
|--------|------|-------------|
| `--limit` | int | Number of insights to display (0=all) |
| `--subscription` | text | Azure subscription ID (substring match) |
| `--status` | choice | new, in_progress, completed, ignored |
| `--created-before` | int | Unix timestamp - created before this |
| `--created-after` | int | Unix timestamp - created after this |
| `--min-cost` | float | Minimum cost impact (inclusive) |
| `--max-cost` | float | Maximum cost impact (inclusive) |
| `--title` | text | Title substring (case-insensitive) |
| `--rec-id` | text | Azure Advisor recommendation ID |
| `--format` | choice | table (default) or json |

**Output Example:**
```
Fetching insights from CloudZero (limit=20)...
Filters applied: 1000 → 15 insights

✓ Displaying 15 of 15+ insights:

--------------------------------------------------------------------------------
1. Right-size VM: vm-firewall-prod (D8ls_v5 → B8als_v2)
   Status: new | Cost Impact: $708 | Source: azure advisor
   Created: 1771351712 | Updated: 1771351712
--------------------------------------------------------------------------------
2. Shutdown vm-test-dev
   Status: new | Cost Impact: $1200 | Source: azure advisor
   Created: 1771351713 | Updated: 1771351713
--------------------------------------------------------------------------------
...
```

**Performance notes:**
- Default limit (10): ~2-5 seconds
- Limit 100: ~10-30 seconds
- Limit 0 (all): 60-120 minutes for 10K-50K insights
- Filters are applied client-side after fetching

---

### Delete Insights

Delete Azure Advisor insights from CloudZero with optional filters.

⚠️ **DESTRUCTIVE OPERATION** - Use with caution!
⚠️ **This command ONLY deletes Azure Advisor insights** - other insight types are never affected.

#### Recommended Workflow: Always Use Dry-Run First

```bash
# Step 1: Preview what will be deleted
python -m app.cli delete --dry-run

# Step 2: Review the output carefully

# Step 3: Actually delete (with confirmation)
python -m app.cli delete

# OR delete without confirmation
python -m app.cli delete --force
```

#### Basic Usage

```bash
# Delete ALL Azure Advisor insights (with confirmation)
python -m app.cli delete

# Preview deletion (no actual changes)
python -m app.cli delete --dry-run

# Delete without confirmation (dangerous!)
python -m app.cli delete --force
```

#### Targeted Deletion with Filters

Use filters to delete specific subsets of insights:

```bash
# Delete by status
python -m app.cli delete --status ignored --dry-run
python -m app.cli delete --status completed --force

# Delete from specific Azure subscription
python -m app.cli delete --subscription sub-abc-123 --dry-run

# Delete low-value insights
python -m app.cli delete --max-cost 50 --dry-run

# Delete high-value insights (be careful!)
python -m app.cli delete --min-cost 1000 --dry-run

# Delete by title pattern
python -m app.cli delete --title "Shutdown" --dry-run

# Delete old insights (Unix timestamp)
python -m app.cli delete --created-before 1705881600 --dry-run

# Combine filters for precise targeting
python -m app.cli delete --status ignored --max-cost 100 --dry-run
```

#### Available Filters

All filters from `list` command work with `delete`:

| Filter | Type | Description |
|--------|------|-------------|
| `--dry-run` | flag | **Preview deletions without actually deleting** |
| `--force` | flag | Skip confirmation prompt |
| `--subscription` | text | Azure subscription ID (substring match) |
| `--status` | choice | new, in_progress, completed, ignored |
| `--created-before` | int | Unix timestamp - delete insights created before this |
| `--created-after` | int | Unix timestamp - delete insights created after this |
| `--min-cost` | float | Minimum cost impact (inclusive) |
| `--max-cost` | float | Maximum cost impact (inclusive) |
| `--title` | text | Title substring (case-insensitive) |
| `--rec-id` | text | Azure Advisor recommendation ID |

**Output Example (Dry-Run):**
```
[DRY RUN] Previewing Azure Advisor insight deletions...

[DRY RUN] Would delete 15 Azure Advisor insights:
  1. Shutdown vm-test-dev ($50)
  2. Right-size VM: vm-old (D4 → B2) ($25)
  3. Shutdown vm-temp ($30)
  ... and 12 more

  Filters: status=ignored, max_cost<=50

[DRY RUN] No insights were actually deleted
```

**Output Example (Actual Deletion):**
```
Deleting Azure Advisor insights from CloudZero...

⚠️  Found 15 Azure Advisor insights to delete:
  1. Shutdown vm-test-dev ($50)
  2. Right-size VM: vm-old (D4 → B2) ($25)
  ... and 13 more

  Filters: status=ignored, max_cost<=50

⚠️  WARNING: This will delete 15 Azure Advisor insights from CloudZero!
⚠️  Other CloudZero insights will NOT be affected.
Type 'DELETE' to confirm: DELETE

🗑️  Deleting 15 Azure Advisor insights...

✓ Deleted 15/15 Azure Advisor insights
```

**When to use:**
- Cleaning up test runs
- Removing old insights before v2.0 upgrade
- Resetting to fresh state
- Removing addressed/ignored insights
- Cleaning up low-value recommendations

**Safety features:**
- **Dry-run mode** - preview before deleting
- Interactive confirmation required (unless --force)
- **Source locked** - only touches "azure advisor" insights
- **Filter preview** - shows which filters are applied
- Paranoid double-checks before each deletion
- Reports success/failure counts

---

## Use Cases

### Daily Automated Sync

Schedule the tool to run daily and automatically sync new Azure recommendations.

```bash
# In cron or scheduled job
make validate && make dry-run && make run-sync
```

**Recommended:**
- Run during off-hours (2-4 AM)
- First check credentials with `validate`
- Use `dry-run` to preview (optional but recommended)
- Then run `sync` to upload new recommendations

See [DEPLOYMENT.md](DEPLOYMENT.md) for scheduling examples.

### One-Time Audit

Export all recommendations to CSV for offline analysis:

```bash
make run-export
```

Then analyze `./output/azure_advisor_recommendations.csv` in Excel or other tools.

### Migration from v1.x

If upgrading from v1.x with collapsed insights:

```bash
# 1. Export current state for backup
make run-list LIMIT=0 > insights_backup.txt

# 2. Delete old collapsed insights
make run-delete  # Confirm deletion

# 3. Sync with new 1:1 mapping
make dry-run     # Preview
make run-sync    # Upload
```

### Testing Credentials

Before deploying to production:

```bash
# Test Azure credentials
python -m app.cli validate --azure

# Test CloudZero credentials
python -m app.cli validate --cloudzero

# Test both
python -m app.cli validate
```

### Preview Changes

Before any sync:

```bash
# Always dry-run first
make dry-run

# Review output, then sync
make run-sync
```

---

## Understanding the Output

### Sync Output Explained

```
Initializing Azure and CloudZero clients...     # Creating API clients
Fetching Azure subscriptions...                 # Listing accessible subscriptions
✓ Found 3 subscription(s)                       # Number of subscriptions found

Fetching Azure Advisor recommendations...        # Fetching from Azure Advisor API
✓ Retrieved 156 recommendation(s)               # Total recommendations across all subs

Checking for existing insights in CloudZero...   # Fetching CloudZero insights
✓ 42 new recommendation(s) to sync              # After filtering duplicates

Syncing recommendations  [####]  42/42          # Progress bar

✓ Successfully created 42 insight(s)            # Final count
```

### Common Status Messages

| Message | Meaning |
|---------|---------|
| `✓ Found N subscription(s)` | Azure authentication succeeded |
| `✓ Retrieved N recommendation(s)` | Azure Advisor API call succeeded |
| `✓ N new recommendation(s) to sync` | After duplicate filtering |
| `ℹ All recommendations already exist` | Nothing new to sync |
| `⚠ N insight(s) failed` | Some uploads failed (check logs) |
| `❌ Error: CLOUDZERO_API_KEY required` | Missing environment variable |

### Log Levels

The tool uses Python logging with these levels:

- **INFO**: Normal operations (subscription fetching, insight creation)
- **WARNING**: Non-critical issues (malformed recommendations, partial failures)
- **ERROR**: Failures (API errors, authentication issues)
- **DEBUG**: Detailed diagnostic info (not shown by default)

---

## Best Practices

### 1. Always Validate First

```bash
make validate
```

Ensures credentials are working before attempting sync.

### 2. Use Dry-Run Before Sync

```bash
make dry-run        # Preview
make run-sync       # Then sync
```

Prevents unexpected uploads.

### 3. Schedule During Off-Hours

First run can take 60-120 minutes for large deployments:

```bash
# In cron: Run daily at 3 AM
0 3 * * * cd /path/to/project && make run-sync
```

### 4. Monitor Logs

```bash
# View logs for troubleshooting
docker logs <container-id>

# Or redirect to file
make run-sync > sync.log 2>&1
```

### 5. Use Limit for Quick Checks

```bash
# Quick check (fast)
make run-list LIMIT=10

# Full list (slow)
make run-list LIMIT=0
```

### 6. Export for Auditing

```bash
# Regular exports for historical tracking
make run-export
mv output/azure_advisor_recommendations.csv backups/recommendations_$(date +%Y%m%d).csv
```

### 7. Clean Up Test Data

```bash
# After testing
make run-delete
```

---

## Troubleshooting

### "CLOUDZERO_API_KEY environment variable is required"

**Cause:** Missing CloudZero API key

**Solution:**
```bash
# Check .env file exists
cat .env | grep CLOUDZERO_API_KEY

# Ensure Docker is loading .env
docker run --rm --env-file .env cloudzero-azure-insights env | grep CLOUDZERO
```

### "Azure: Invalid - ..."

**Cause:** Azure credentials missing or invalid

**Solution:**
```bash
# Validate Azure setup
make validate

# Check environment variables
cat .env | grep AZURE

# Test Azure CLI
az account list  # If using Azure CLI
```

### "No Azure subscriptions found"

**Cause:** Service principal lacks Reader role

**Solution:**
- Ensure service principal has "Reader" role on target subscriptions
- Check Azure portal → Subscriptions → Access Control (IAM)
- See [DEPLOYMENT.md](DEPLOYMENT.md) for permission setup

### Sync Takes Too Long

**Cause:** Large number of existing CloudZero insights (10K-50K+)

**Solution:**
- This is normal for first run
- Schedule during off-hours
- Progress is saved incrementally
- Subsequent runs are faster (only new recommendations)

### "Failed to create insight"

**Cause:** CloudZero API error

**Solution:**
```bash
# Check API status
curl -H "Authorization: $CLOUDZERO_API_KEY" https://api.cloudzero.com/v2/insights?limit=1

# Verify API key is valid
make validate

# Check logs for specific error
docker logs <container-id> | grep ERROR
```

### Import Error: No module named 'click'

**Cause:** Click not installed

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or install Click directly
pip install click==8.1.7
```

### "Deprecation Warning" When Using Old Commands

**Cause:** Using v1.x flag-based CLI

**Solution:** Migrate to v2.0 subcommands:

```bash
# Old
python -m app.app --transmit --dry-run

# New
python -m app.cli sync --dry-run
```

See [CLI Migration Guide](../README.md#cli-migration-guide) in README.

---

## Getting Help

### Command Help

```bash
# Show all commands
python -m app.cli --help

# Command-specific help
python -m app.cli sync --help
python -m app.cli export --help
python -m app.cli list --help
python -m app.cli delete --help
python -m app.cli validate --help
```

### Makefile Help

```bash
make help
```

### Additional Resources

- [README](../README.md) - Overview and quick start
- [DEPLOYMENT.md](DEPLOYMENT.md) - Scheduling and deployment
- [CLI Design](design/cli-subcommand-analysis.md) - Technical design details
- [GitHub Issues](https://github.com/cloudzero/cz-azure-insights/issues) - Bug reports and feature requests
- [support@cloudzero.com](mailto:support@cloudzero.com) - CloudZero support team
