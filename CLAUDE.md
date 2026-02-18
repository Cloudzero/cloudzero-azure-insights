# CloudZero Azure Insights - Development Guidelines

This file contains project-specific instructions for AI-assisted development. These guidelines OVERRIDE default behavior and must be followed exactly.

## Table of Contents

- [Coding Guidelines](#coding-guidelines)
- [Python-Specific Guidelines](#python-specific-guidelines)
- [Docker Guidelines](#docker-guidelines)
- [Documentation Guidelines](#documentation-guidelines)
- [AI-Assisted Development Workflow](#ai-assisted-development-workflow)
- [Git Workflow](#git-workflow)
- [Testing Guidelines](#testing-guidelines)

## Coding Guidelines

### Core Principles

- **KISS**: Keep it simple - solve the problem at hand, not future problems
- **Single Responsibility**: Each component should do one thing well
- **Avoid God Classes/Functions**: Classes with 200+ lines or 5+ methods doing unrelated things should be split. Functions over 50 lines should be decomposed into smaller, focused functions
- **Clear Dependencies**: Inject dependencies, don't create them internally
- **Performance First**: Optimize for time, memory, and disk usage from the start
- **Fail Fast**: Validate early, provide clear error messages
- **Meaningful Names**: Use clear, descriptive variable and function names
- **Testability**: Design code that's easy to test and mock
- **No Dead Code**: Remove unused imports, methods, and commented code immediately

### Method Rules

- **Maximum 50 lines per method**
- **Maximum 3 levels of nesting**
- **Single responsibility** (no "and" in method names)
- **Inject dependencies, don't create them**

### File and Class Size Limits

- **Maximum ~300 lines per module** (guideline, not hard limit)
- **Maximum ~150 lines per class** - Split into multiple classes if exceeded
- **Split files when they serve 3+ distinct responsibilities**
- Consider refactoring when:
  - A single file exceeds 500 lines
  - A class has 5+ unrelated methods
  - Multiple independent concerns are mixed (API clients, data transformation, CLI, etc.)

### Code Quality Checklist

Before committing, verify:
- [ ] All methods under 50 lines
- [ ] No god classes (classes under ~150 lines with focused responsibilities)
- [ ] No god functions (functions over 50 lines decomposed into helpers)
- [ ] Files serving 3+ responsibilities have been split
- [ ] Nesting depth ≤ 3 levels
- [ ] Dependencies injected, not created
- [ ] No unused imports or dead code
- [ ] Clear error messages for all failure paths
- [ ] Descriptive variable/function names (no single letters except loop indices)

## Python-Specific Guidelines

### Style and Structure

- Follow **PEP 8** with these additions:
  - Max line length: 100 characters (not 79)
  - Use double quotes for strings (except to avoid escaping)
  - Absolute imports preferred over relative imports

### Type Hints

- **Required for all public functions and methods**
- Use `typing` module annotations: `List`, `Dict`, `Optional`, `Union`
- Return types always specified

```python
from typing import List, Dict, Optional

def process_recommendations(
    recommendations: List[Dict[str, str]],
    threshold: Optional[float] = None
) -> Dict[str, int]:
    """Process Azure recommendations and return summary."""
    pass
```

### Docstrings

- **Required for all public classes, methods, and functions**
- Use **Google style** docstrings
- Include Args, Returns, Raises sections

```python
def fetch_advisor_data(subscription_id: str, client: AdvisorManagementClient) -> List[Dict]:
    """Fetch cost recommendations from Azure Advisor.

    Args:
        subscription_id: Azure subscription identifier
        client: Authenticated Azure Advisor client (injected dependency)

    Returns:
        List of recommendation dictionaries with cost savings data

    Raises:
        AzureError: If API call fails or credentials invalid
        ValueError: If subscription_id is empty or malformed
    """
    pass
```

### Error Handling

- **Fail fast**: Validate inputs at function entry
- **Specific exceptions**: Don't catch generic `Exception`
- **Clear messages**: Include context (what failed, why, how to fix)

```python
# Good
if not subscription_id:
    raise ValueError(
        "subscription_id cannot be empty. "
        "Ensure AZURE_SUBSCRIPTION_ID is set in environment."
    )

# Bad
if not subscription_id:
    raise Exception("Invalid input")
```

### Logging

- Use Python's `logging` module (already configured in project)
- Log levels:
  - `DEBUG`: Detailed diagnostic info
  - `INFO`: General operational events
  - `WARNING`: Unexpected but handled situations
  - `ERROR`: Failures requiring attention
- Include context in log messages

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Fetching recommendations for subscription: {subscription_id}")
logger.error(f"Failed to upload insight {insight_id} to CloudZero: {error}", exc_info=True)
```

### Dependencies and Imports

- Group imports in order: stdlib, third-party, local
- One import per line for readability
- Remove unused imports immediately

```python
# Standard library
import logging
from typing import List, Dict

# Third-party
from azure.identity import DefaultAzureCredential
from azure.mgmt.advisor import AdvisorManagementClient

# Local
from app.models import Insight
from app.utils import format_currency
```

## Docker Guidelines

### Dockerfile Best Practices

- **Multi-stage builds**: Separate build and runtime stages
- **Layer caching**: Order commands from least to most frequently changed
- **Minimal images**: Use `python:3.11-slim` (not `python:3.11`)
- **Security**: Don't run as root, use non-root user
- **Dependencies first**: Copy requirements.txt before code

```dockerfile
# Good layer ordering
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER nonroot
```

### Environment Variables

- **Never hardcode secrets** in Dockerfile or code
- Use `.env` file for local development (already gitignored)
- Required variables should be documented and validated at startup

```python
# Validate required env vars at startup
required_vars = ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "CLOUDZERO_API_KEY"]
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
```

### Container Efficiency

- Keep images small (<200MB for Python apps)
- Use `.dockerignore` to exclude unnecessary files
- Combine RUN commands to reduce layers

## Documentation Guidelines

### Size Limits

- **General docs**: Split at 300 lines
- **Hard limit**: 400 lines (500 for implementation guides only)
- **README.md**: Must stay under 150 lines
- **CHANGELOG.md**: Unlimited, but structured by version

### When to Split Documentation

Split a document when it:
- Crosses 300 lines
- Covers 2+ distinct concerns
- Has 5+ major sections
- Serves multiple audiences (developers vs. operators)

### Multi-File Documentation Structure

For complex topics, use this structure:

```
docs/{category}/{topic}/
├── README.md           # Overview, <150 lines
├── design.md           # Architecture decisions, <400 lines
├── implementation.md   # How to build, <500 lines
└── operations.md       # How to run/maintain, <400 lines
```

Example categories:
- `docs/architecture/` - System design, component interactions
- `docs/development/` - Setup, coding guides, detailed guidelines
- `docs/design/` - Feature designs created during AI discussions
- `docs/operations/` - Deployment, monitoring, troubleshooting

### Documentation Style

- **Concise over comprehensive**: Get to the point quickly
- **Easy to scan**: Use bullets, headers, clear structure
- **Code examples**: Show don't tell
- **Purpose-driven**: Every doc should answer "why does this exist?"

### README.md Maintenance

Keep the main README.md focused:
- What the project does (2-3 sentences)
- Quick start (< 5 steps)
- Links to detailed docs
- Support and contribution info

Move detailed content to `docs/`:
- Architecture details → `docs/architecture/`
- Development setup → `docs/development/`
- API reference → `docs/api/`

## AI-Assisted Development Workflow

This project uses AI-assisted development with specific workflows designed for efficiency and consistency across sessions.

### Core Pattern: Guidelines → Design → Documentation → Implementation

1. **Guidelines establish vocabulary** (this file + detailed guides)
2. **Design discussions** explore problems and solutions
3. **Documentation captures decisions** before code (AI-optimized, 300-line limit)
4. **Implementation follows design** with git discipline

### Why This Works

- **Memory efficiency**: AI reads guidelines + design docs, understands full context
- **Cross-session continuity**: Docs persist, AI sessions don't
- **Consistency**: Guidelines prevent re-teaching fundamentals
- **Iteration speed**: Design before code catches issues early (cheaper to fix)

### Session Workflow

1. AI reads `CLAUDE.md` + relevant detailed guides from `docs/development/`
2. Design discussions produce AI-optimized docs (split at 300 lines)
3. Create feature branch (`feature/`, `fix/`, `refactor/`, `investigate/`)
4. Implement following design docs
5. Commit frequently with clear messages
6. Design docs enable next session to continue seamlessly

### Documentation as Memory

- **CLAUDE.md**: Quick reference (this file, ~300 lines)
- **docs/development/**: Detailed guides loaded as needed
- **docs/design/**: Feature designs created during AI discussions
- **docs/architecture/**: System architecture (long-lived reference)

Each doc is sized for AI comprehension (<400 lines), enabling selective loading based on current task.

## Git Workflow

### Branch Naming

- `feature/` - New functionality
- `fix/` - Bug fixes
- `refactor/` - Code improvements without behavior change
- `investigate/` - Exploratory work
- `docs/` - Documentation-only changes

Examples: `feature/csv-export`, `fix/azure-auth`, `refactor/insight-mapper`

### Commit Messages

- Use imperative mood: "Add CSV export" not "Added CSV export"
- First line <72 characters (summary)
- Blank line, then detailed explanation if needed
- Reference issues: "Fixes #123" or "Related to #456"

```
Add CSV export functionality for Azure recommendations

- Create CSVExporter class with dependency injection
- Add export_to_csv() method to main workflow
- Update README with new make target
- Add tests for CSV formatting

Fixes #42
```

### Commit Frequency

- **Commit often**: Each logical unit of work
- **Working state**: Every commit should pass tests
- **Atomic changes**: One concern per commit

Good commit sequence:
1. "Add CSVExporter class with tests"
2. "Integrate CSVExporter into main workflow"
3. "Add Makefile target for CSV export"
4. "Update README with CSV export documentation"

## Testing Guidelines

### Test Coverage Requirements

- **All new code must have tests**
- **Public functions**: 100% coverage required
- **Private functions**: Test through public API
- **Happy path + error cases**: Both required

### Test Structure

- Use `pytest` (already in requirements.txt)
- Test files: `test_*.py` or `*_test.py`
- One test file per module: `app/insights.py` → `tests/test_insights.py`

### Test Naming

Use descriptive names that explain what's being tested:

```python
def test_fetch_recommendations_returns_list_when_successful():
    """fetch_recommendations should return list of dicts when API succeeds."""
    pass

def test_fetch_recommendations_raises_azure_error_when_unauthorized():
    """fetch_recommendations should raise AzureError with clear message when credentials invalid."""
    pass
```

### Mocking Dependencies

- **Always mock external services**: Azure API, CloudZero API
- **Use dependency injection**: Makes mocking easy
- **Test behavior, not implementation**

```python
from unittest.mock import Mock, patch

def test_upload_insights_calls_api_with_correct_data():
    """upload_insights should POST insights to CloudZero API."""
    # Arrange
    mock_client = Mock()
    insights = [{"id": "123", "type": "cost"}]
    uploader = InsightUploader(client=mock_client)  # Injected dependency

    # Act
    uploader.upload(insights)

    # Assert
    mock_client.post.assert_called_once_with("/insights", json=insights)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_insights.py

# Run specific test
pytest tests/test_insights.py::test_upload_insights_calls_api_with_correct_data
```

---

## Project-Specific Context

### CloudZero Integration

- **Insights API**: POST to `/insights` endpoint
- **Idempotency**: Check existing insights before uploading (avoid duplicates)
- **Rate limiting**: Respect API limits (currently not enforced, but design for it)

### Azure Advisor Integration

- **Authentication**: Use `DefaultAzureCredential` (supports multiple auth methods)
- **Subscriptions**: Support multiple subscriptions (iterate and aggregate)
- **Recommendation types**: Focus on "Cost" category only

### Security Considerations

- **Never log credentials**: Mask or omit from logs
- **Environment variables**: Validate presence at startup, fail fast if missing
- **API keys**: Never commit to git (check with `.gitignore`)
- **Docker**: Don't run as root user

---

**Last Updated**: 2026-02-17
**Maintained By**: Development team with AI assistance
