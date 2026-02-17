# CLI Subcommand Design Analysis

**Status:** Design Discussion
**Date:** 2026-02-17
**Context:** Refactoring flat flag CLI to subcommand structure

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Subcommand Design Patterns](#subcommand-design-patterns)
3. [Implementation Approaches](#implementation-approaches)
4. [Detailed Design Options](#detailed-design-options)
5. [Migration Strategy](#migration-strategy)
6. [Recommendation](#recommendation)

---

## Current State Analysis

### Current CLI Structure

```bash
python -m app.app [FLAGS]

Flags:
  --transmit          # Sync to CloudZero
  --export-csv        # Export to CSV
  --list-insights     # List existing insights
  --limit N           # Limit for list (only)
  --dry-run           # Preview mode (transmit only)
```

### Problems with Current Design

#### 1. **Flat Structure Doesn't Scale**

```bash
# Current: Unclear what operations exist
python -m app.app --help
# Shows: --transmit, --export-csv, --list-insights, --dry-run, --limit

# What if we add:
# --delete-insights, --validate-credentials, --export-json,
# --sync-subscriptions, --generate-report, --cleanup-old
# Result: 10+ top-level flags, hard to scan
```

#### 2. **Flag Interactions Are Implicit**

```bash
# Valid combinations not documented:
python -m app.app --transmit --export-csv  # Both? Sequential?
python -m app.app --transmit --dry-run     # Dry-run applies to transmit
python -m app.app --export-csv --dry-run   # Does dry-run apply here?
python -m app.app --list-insights --limit 20  # Limit only works with list
```

#### 3. **Naming Inconsistency**

```bash
--transmit         # Verb
--list-insights    # Verb + noun
--export-csv       # Verb + format
--dry-run          # Adjective + noun
```

#### 4. **Context-Dependent Flags**

```bash
--limit N          # Only meaningful with --list-insights
--dry-run          # Only applies to --transmit
# These should be subcommand-specific, not global
```

#### 5. **No Room for Advanced Features**

```bash
# Future features awkward to add:
--transmit --delete-duplicates --backup-first --notify-slack
# vs subcommands:
sync --delete-duplicates --backup --notify slack
```

---

## Subcommand Design Patterns

### Pattern 1: Git-Style (Verb Subcommands)

**Structure:** `program <verb> [options]`

```bash
git commit -m "message"
git push origin main
git log --oneline
```

**Characteristics:**
- Verbs as subcommands
- Natural language flow
- Widely understood pattern

**Applied to our tool:**
```bash
cz-azure sync --dry-run
cz-azure export csv
cz-azure list --limit 20
cz-azure delete --filter "source=azure"
```

### Pattern 2: Kubectl-Style (Resource + Verb)

**Structure:** `program <verb> <noun> [options]`

```bash
kubectl get pods
kubectl delete deployment my-app
kubectl describe node worker-1
```

**Characteristics:**
- Verb-noun pairs
- Resource-oriented
- More structured

**Applied to our tool:**
```bash
cz-azure sync recommendations --dry-run
cz-azure export recommendations --format csv
cz-azure list insights --limit 20
cz-azure delete insights --source azure
```

### Pattern 3: Docker-Style (Noun Subcommands)

**Structure:** `program <noun> <verb> [options]`

```bash
docker container run nginx
docker image build -t myapp .
docker network create my-net
```

**Characteristics:**
- Noun-first hierarchy
- Groups related operations
- Good for multiple resource types

**Applied to our tool:**
```bash
cz-azure insights sync --dry-run
cz-azure insights list --limit 20
cz-azure insights delete --filter "source=azure"
cz-azure recommendations export csv
```

### Pattern 4: AWS CLI-Style (Service + Action)

**Structure:** `program <service> <action> [options]`

```bash
aws ec2 describe-instances
aws s3 sync s3://bucket ./local
aws lambda invoke --function-name my-func
```

**Characteristics:**
- Service namespaces
- Action verbs (often hyphenated)
- Very explicit

**Applied to our tool:**
```bash
cz-azure cloudzero sync-insights --dry-run
cz-azure cloudzero list-insights --limit 20
cz-azure advisor export-recommendations --format csv
```

---

## Implementation Approaches

### Approach A: argparse with Subparsers (Native Python)

**Implementation:**

```python
import argparse

def main():
    parser = argparse.ArgumentParser(
        prog="cz-azure",
        description="CloudZero Azure Advisor Integration"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sync command
    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync Azure recommendations to CloudZero"
    )
    sync_parser.add_argument("--dry-run", action="store_true")
    sync_parser.add_argument("--delete-duplicates", action="store_true")

    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export Azure recommendations"
    )
    export_parser.add_argument("format", choices=["csv", "json"])
    export_parser.add_argument("--output", "-o", default="output/")

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List existing CloudZero insights"
    )
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.add_argument("--filter", help="Filter by source")

    # Delete command
    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete insights from CloudZero"
    )
    delete_parser.add_argument("--filter", required=True)
    delete_parser.add_argument("--force", action="store_true")

    args = parser.parse_args()

    if args.command == "sync":
        sync_command(args)
    elif args.command == "export":
        export_command(args)
    # ... etc
```

**Pros:**
- No external dependencies
- Part of stdlib
- Works with existing project structure

**Cons:**
- Verbose boilerplate
- Subparser help text handling clunky
- Limited validation features
- No automatic command discovery

**Usage:**
```bash
python -m app.app sync --dry-run
python -m app.app export csv --output ./reports
python -m app.app list --limit 20 --filter "source=azure"
python -m app.app delete --filter "source=azure" --force
python -m app.app --help
python -m app.app sync --help
```

---

### Approach B: Click Framework (Decorator-Based)

**Implementation:**

```python
import click

@click.group()
def cli():
    """CloudZero Azure Advisor Integration"""
    pass

@cli.command()
@click.option("--dry-run", is_flag=True, help="Preview without uploading")
@click.option("--delete-duplicates", is_flag=True)
def sync(dry_run, delete_duplicates):
    """Sync Azure recommendations to CloudZero"""
    if dry_run:
        click.echo("DRY RUN mode enabled")
    transmit_azure_insights(dry_run=dry_run)

@cli.command()
@click.argument("format", type=click.Choice(["csv", "json"]))
@click.option("--output", "-o", default="output/")
def export(format, output):
    """Export Azure recommendations"""
    if format == "csv":
        export_to_csv(output)
    elif format == "json":
        export_to_json(output)

@cli.command()
@click.option("--limit", type=int, default=10, help="Number of insights to show")
@click.option("--filter", help="Filter by source")
def list(limit, filter):
    """List existing CloudZero insights"""
    display_insights(limit=limit, filter=filter)

@cli.command()
@click.option("--filter", required=True, help="Filter insights to delete")
@click.option("--force", is_flag=True, help="Skip confirmation")
def delete(filter, force):
    """Delete insights from CloudZero"""
    delete_insights(filter=filter, force=force)

if __name__ == "__main__":
    cli()
```

**Pros:**
- Clean, readable code
- Excellent help text generation
- Built-in validation
- Composable (can group commands)
- Progress bars, colors, prompts built-in

**Cons:**
- External dependency (though widely used)
- Decorator magic can be confusing
- Global state with `@click.pass_context`

**Usage:**
```bash
python -m app.app sync --dry-run
python -m app.app export csv --output ./reports
python -m app.app list --limit 20 --filter "source=azure"
python -m app.app delete --filter "source=azure" --force
```

**Help Output:**
```
Usage: app.py [OPTIONS] COMMAND [ARGS]...

  CloudZero Azure Advisor Integration

Options:
  --help  Show this message and exit.

Commands:
  delete  Delete insights from CloudZero
  export  Export Azure recommendations
  list    List existing CloudZero insights
  sync    Sync Azure recommendations to CloudZero
```

---

### Approach C: Typer Framework (Type-Hints Based)

**Implementation:**

```python
import typer
from typing import Optional
from enum import Enum

app = typer.Typer(help="CloudZero Azure Advisor Integration")

class ExportFormat(str, Enum):
    csv = "csv"
    json = "json"

@app.command()
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without uploading"),
    delete_duplicates: bool = typer.Option(False, help="Remove duplicates first")
):
    """Sync Azure recommendations to CloudZero"""
    if dry_run:
        typer.echo("DRY RUN mode enabled")
    transmit_azure_insights(dry_run=dry_run)

@app.command()
def export(
    format: ExportFormat = typer.Argument(..., help="Export format"),
    output: str = typer.Option("output/", "-o", "--output", help="Output directory")
):
    """Export Azure recommendations"""
    if format == ExportFormat.csv:
        export_to_csv(output)
    elif format == ExportFormat.json:
        export_to_json(output)

@app.command()
def list(
    limit: int = typer.Option(10, help="Number of insights to show"),
    filter: Optional[str] = typer.Option(None, help="Filter by source")
):
    """List existing CloudZero insights"""
    display_insights(limit=limit, filter=filter)

@app.command()
def delete(
    filter: str = typer.Option(..., help="Filter insights to delete"),
    force: bool = typer.Option(False, help="Skip confirmation")
):
    """Delete insights from CloudZero"""
    if not force:
        confirm = typer.confirm("Are you sure you want to delete?")
        if not confirm:
            raise typer.Abort()
    delete_insights(filter=filter, force=force)

if __name__ == "__main__":
    app()
```

**Pros:**
- Modern Python (type hints)
- Better IDE support (autocomplete)
- Automatic validation from types
- Built on Click (inherits features)
- Less boilerplate than Click

**Cons:**
- External dependency
- Requires Python 3.6+
- Type hints required (learning curve)

**Usage:** Same as Click

---

### Approach D: Fire Framework (Zero-Config)

**Implementation:**

```python
import fire

class CLI:
    """CloudZero Azure Advisor Integration"""

    def sync(self, dry_run=False, delete_duplicates=False):
        """Sync Azure recommendations to CloudZero

        Args:
            dry_run: Preview without uploading
            delete_duplicates: Remove duplicates first
        """
        if dry_run:
            print("DRY RUN mode enabled")
        transmit_azure_insights(dry_run=dry_run)

    def export(self, format="csv", output="output/"):
        """Export Azure recommendations

        Args:
            format: Export format (csv or json)
            output: Output directory
        """
        if format == "csv":
            export_to_csv(output)
        elif format == "json":
            export_to_json(output)

    def list(self, limit=10, filter=None):
        """List existing CloudZero insights

        Args:
            limit: Number of insights to show
            filter: Filter by source
        """
        display_insights(limit=limit, filter=filter)

    def delete(self, filter=None, force=False):
        """Delete insights from CloudZero

        Args:
            filter: Filter insights to delete
            force: Skip confirmation
        """
        if not filter:
            raise ValueError("--filter is required")
        delete_insights(filter=filter, force=force)

if __name__ == "__main__":
    fire.Fire(CLI)
```

**Pros:**
- Minimal boilerplate
- Automatic CLI from any class/function
- Very Pythonic
- Docstrings become help text

**Cons:**
- Less control over CLI structure
- Unusual flag syntax (`--flag=value` required, not `--flag value`)
- Help text not as polished
- Magic can be confusing

**Usage:**
```bash
python -m app.app sync --dry-run
python -m app.app export --format=csv --output=./reports
python -m app.app list --limit=20 --filter="source=azure"
```

---

## Detailed Design Options

### Option 1: Simple Verb Commands (Git-Style)

**Structure:**
```
cz-azure <command> [options]

Commands:
  sync        Sync recommendations to CloudZero
  export      Export recommendations to file
  list        List existing insights
  delete      Delete insights from CloudZero
  validate    Validate credentials and permissions
```

**Full Command Tree:**

```bash
# Sync command
cz-azure sync [--dry-run] [--delete-duplicates] [--notify EMAIL]

# Export command
cz-azure export <format> [--output DIR]
  formats: csv, json

# List command
cz-azure list [--limit N] [--filter EXPR] [--sort FIELD] [--format TABLE|JSON]

# Delete command
cz-azure delete --filter EXPR [--force] [--backup]

# Validate command
cz-azure validate [--azure] [--cloudzero] [--all]
```

**Example Usage:**
```bash
# Daily sync workflow
cz-azure validate --all
cz-azure sync --dry-run
cz-azure sync
cz-azure list --limit 5

# Cleanup workflow
cz-azure list --filter "source=azure advisor" --format json > insights.json
cz-azure delete --filter "status=addressed" --force

# Export workflow
cz-azure export csv --output ./reports/
cz-azure export json --output ./backup/
```

**Pros:**
- Simple mental model
- Natural language
- Easy to discover
- Direct verb-to-action mapping

**Cons:**
- Flat command space (doesn't group related operations)
- Could grow large (20+ commands)

---

### Option 2: Resource-Based Commands (Docker-Style)

**Structure:**
```
cz-azure <resource> <action> [options]

Resources:
  insights        CloudZero insights operations
  recommendations Azure recommendations operations
  config          Configuration management
```

**Full Command Tree:**

```bash
# Insights resource
cz-azure insights sync [--dry-run]
cz-azure insights list [--limit N] [--filter EXPR]
cz-azure insights delete --filter EXPR [--force]
cz-azure insights export <format> [--output DIR]

# Recommendations resource
cz-azure recommendations fetch [--subscriptions ID,ID]
cz-azure recommendations export <format> [--output DIR]
cz-azure recommendations analyze [--group-by FIELD]

# Config resource
cz-azure config validate
cz-azure config show
cz-azure config set KEY VALUE
```

**Example Usage:**
```bash
# Work with insights
cz-azure insights sync --dry-run
cz-azure insights list --limit 20
cz-azure insights delete --filter "source=azure"

# Work with recommendations
cz-azure recommendations fetch
cz-azure recommendations analyze --group-by subscription

# Configuration
cz-azure config validate
cz-azure config show
```

**Pros:**
- Groups related operations
- Clear resource ownership
- Scales well (can add resources)
- Predictable structure

**Cons:**
- More verbose
- Noun-verb vs verb-noun debate
- Extra typing for common operations

---

### Option 3: Hybrid Approach (Convenience + Structure)

**Structure:**
```
cz-azure <command> [options]

Commands:
  # Convenience shortcuts (most common)
  sync        Sync to CloudZero (alias for insights sync)
  list        List insights (alias for insights list)

  # Structured commands
  insights    Manage CloudZero insights
  recs        Manage Azure recommendations
  config      Configuration and validation
```

**Full Command Tree:**

```bash
# Convenience commands (top-level)
cz-azure sync [--dry-run]         # Most common operation
cz-azure list [--limit N]          # Second most common

# Insights subcommands
cz-azure insights sync [--dry-run]
cz-azure insights list [--limit N]
cz-azure insights delete --filter EXPR
cz-azure insights export <format>

# Recommendations subcommands
cz-azure recs fetch
cz-azure recs export <format>
cz-azure recs analyze

# Config subcommands
cz-azure config validate
cz-azure config show
```

**Example Usage:**
```bash
# Quick operations (shortcuts)
cz-azure sync --dry-run
cz-azure list --limit 20

# Advanced operations (full paths)
cz-azure insights delete --filter "status=addressed"
cz-azure recs analyze --group-by subscription
cz-azure config validate --azure
```

**Pros:**
- Best of both worlds
- Beginner-friendly shortcuts
- Advanced users get structure
- Backward compatibility easier

**Cons:**
- Two ways to do same thing (confusion)
- More commands to document
- Aliases might diverge over time

---

## Migration Strategy

### Phase 1: Add Subcommands (Backward Compatible)

**Support both syntaxes:**

```python
def main():
    args = sys.argv[1:]

    # Detect old-style flags
    if any(arg.startswith("--") for arg in args) and not any(arg in COMMANDS for arg in args):
        # Old style: python -m app.app --transmit --dry-run
        warnings.warn("Flag-based syntax deprecated, use: cz-azure sync --dry-run")
        run_legacy_mode(args)
    else:
        # New style: python -m app.app sync --dry-run
        run_subcommand_mode(args)
```

**Example:**
```bash
# Old (still works, shows warning)
python -m app.app --transmit --dry-run
# Warning: Flag-based syntax deprecated, use: cz-azure sync --dry-run

# New (preferred)
python -m app.app sync --dry-run
```

### Phase 2: Update Documentation

- Update README with new commands
- Add deprecation notices to old flags
- Provide migration guide
- Update Makefile targets

### Phase 3: Deprecation Period

- Set deprecation timeline (e.g., 6 months)
- Log warnings for old syntax
- Track usage metrics
- Communicate to users

### Phase 4: Remove Legacy

- Remove old flag handling
- Clean up code
- Update version (3.0.0 - breaking change)

---

## Recommendation

### Best Choice: **Option 1 (Simple Verb Commands) + Click Framework**

**Why:**

1. **Simple verb commands** because:
   - Most natural for this use case
   - Direct mapping: "I want to sync" → `sync`
   - No resource hierarchy needed (single domain)
   - Easy to discover and remember

2. **Click framework** because:
   - Excellent help text (critical for CLI tools)
   - Rich features (colors, progress, prompts)
   - Widely adopted (used by Flask, AWS SAM, etc.)
   - Good balance: powerful but not complex

**Final Command Structure:**

```bash
cz-azure sync [--dry-run] [--delete-duplicates]
cz-azure export {csv|json} [--output DIR]
cz-azure list [--limit N] [--filter EXPR] [--format {table|json}]
cz-azure delete --filter EXPR [--force] [--backup]
cz-azure validate [--azure] [--cloudzero] [--all]
```

**Implementation Roadmap:**

1. Add Click dependency to requirements.txt
2. Create `app/cli.py` with Click commands
3. Keep `app/app.py` as legacy entry point (backward compat)
4. Update Makefile to use new commands
5. Add deprecation warnings
6. Update all documentation
7. Set removal date for legacy syntax

**Code Structure:**

```
app/
├── cli.py           # New Click-based CLI (entry point)
├── app.py           # Legacy support + shared logic
├── commands/        # Command implementations
│   ├── sync.py
│   ├── export.py
│   ├── list.py
│   └── delete.py
├── clients/         # Existing clients
├── transformers/    # Existing transformers
└── exporters/       # Existing exporters
```

---

## Appendix: Command Reference

### Proposed Final CLI

```
cz-azure - CloudZero Azure Advisor Integration

USAGE:
    cz-azure <COMMAND> [OPTIONS]

COMMANDS:
    sync        Sync Azure Advisor recommendations to CloudZero
    export      Export recommendations to file (csv, json)
    list        List existing CloudZero insights
    delete      Delete insights from CloudZero
    validate    Validate Azure and CloudZero credentials
    version     Show version information

SYNC OPTIONS:
    --dry-run                Preview without uploading
    --delete-duplicates      Remove duplicates before sync
    --notify <EMAIL>         Send notification on completion

EXPORT OPTIONS:
    <format>                 csv or json (required)
    --output <DIR>           Output directory (default: ./output)

LIST OPTIONS:
    --limit <N>              Number of insights (default: 10, 0=all)
    --filter <EXPR>          Filter expression (e.g., "source=azure")
    --sort <FIELD>           Sort by field (title, cost_impact, created)
    --format <FMT>           Output format: table or json

DELETE OPTIONS:
    --filter <EXPR>          Filter expression (required)
    --force                  Skip confirmation prompt
    --backup                 Backup insights before deletion

VALIDATE OPTIONS:
    --azure                  Check Azure credentials only
    --cloudzero              Check CloudZero credentials only
    --all                    Check all credentials (default)

EXAMPLES:
    # Daily sync workflow
    cz-azure validate
    cz-azure sync --dry-run
    cz-azure sync

    # Export and analyze
    cz-azure export csv --output ./reports
    cz-azure list --filter "cost_impact>1000" --format json

    # Cleanup old insights
    cz-azure delete --filter "status=addressed" --backup

ENVIRONMENT VARIABLES:
    AZURE_CLIENT_ID          Azure application client ID
    AZURE_CLIENT_SECRET      Azure application client secret
    AZURE_TENANT_ID          Azure tenant ID
    CLOUDZERO_API_KEY        CloudZero API authentication key

For more information, visit: https://github.com/cloudzero/cz-azure-insights
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-17 | Design document created | Need structured analysis before implementation |
| TBD | Framework selection | Pending team discussion |
| TBD | Migration timeline | After framework selection |

---

**Next Steps:**
1. Review this document with team
2. Decide on framework (Click recommended)
3. Prototype one command
4. Gather feedback
5. Implement full migration
