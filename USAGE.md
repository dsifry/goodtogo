# Good To Go Usage Guide

Complete documentation for the `gtg` CLI tool.

## Installation

```bash
pip install goodtogo
```

### Requirements

- Python 3.9+
- GitHub personal access token with `repo` scope

### Verify Installation

```bash
gtg --version
```

## Authentication

Good To Go needs a GitHub token to access PR data.

### Environment Variable (Recommended)

```bash
export GITHUB_TOKEN=ghp_your_token_here
gtg check owner/repo 123
```

### Command Line Flag

```bash
gtg check owner/repo 123 --token ghp_your_token_here
```

### Creating a Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select the `repo` scope
4. Copy the token and set it as `GITHUB_TOKEN`

## Commands

### `gtg check`

Check if a PR is ready to merge.

```bash
gtg check <owner/repo> <pr_number> [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `owner/repo` | Repository in format `owner/repo` (e.g., `facebook/react`) |
| `pr_number` | Pull request number |

#### Options

| Option | Description |
|--------|-------------|
| `--token`, `-t` | GitHub token (overrides GITHUB_TOKEN env var) |
| `--json`, `-j` | Output results as JSON |
| `--no-cache` | Disable caching (always fetch fresh data) |
| `--verbose`, `-v` | Show detailed output |

#### Examples

```bash
# Basic check
gtg check myorg/myrepo 123

# JSON output for scripting
gtg check myorg/myrepo 123 --json

# Verbose output
gtg check myorg/myrepo 123 --verbose

# Fresh data (no cache)
gtg check myorg/myrepo 123 --no-cache
```

## Exit Codes

Good To Go uses exit codes for deterministic status reporting:

| Code | Status | Description | Action |
|------|--------|-------------|--------|
| 0 | `READY` | PR is ready to merge | Proceed with merge |
| 1 | `ACTION_REQUIRED` | Actionable comments exist | Address the comments |
| 2 | `UNRESOLVED` | Unresolved review threads | Resolve threads |
| 3 | `CI_FAILING` | CI checks failing/pending | Wait for CI or fix failures |
| 4 | `ERROR` | Error fetching data | Check token/connectivity |

### Using Exit Codes in Scripts

```bash
gtg check owner/repo 123
case $? in
  0) echo "Ready to merge!" ;;
  1) echo "Comments need attention" ;;
  2) echo "Threads need resolution" ;;
  3) echo "CI not passing" ;;
  4) echo "Error occurred" ;;
esac
```

## JSON Output Format

With `--json`, Good To Go outputs structured data:

```json
{
  "status": "ACTION_REQUIRED",
  "pr_number": 123,
  "repo_owner": "myorg",
  "repo_name": "myrepo",
  "latest_commit_sha": "abc123...",
  "latest_commit_timestamp": "2024-01-15T10:30:00Z",
  "ci_status": {
    "state": "success",
    "total_checks": 5,
    "passed": 5,
    "failed": 0,
    "pending": 0,
    "checks": [
      {"name": "build", "status": "success", "conclusion": "success", "url": "..."},
      {"name": "test", "status": "success", "conclusion": "success", "url": "..."}
    ]
  },
  "threads": {
    "total": 3,
    "resolved": 2,
    "unresolved": 1,
    "outdated": 0
  },
  "actionable_comments": [
    {
      "id": "123",
      "author": "coderabbitai[bot]",
      "reviewer_type": "coderabbit",
      "body": "Critical: SQL injection vulnerability...",
      "classification": "ACTIONABLE",
      "priority": "CRITICAL",
      "file_path": "src/db.py",
      "line_number": 42
    }
  ],
  "ambiguous_comments": [],
  "action_items": [
    "Fix CRITICAL comment from coderabbit in src/db.py:42"
  ],
  "needs_action": true
}
```

## Comment Classification

Good To Go classifies comments from automated reviewers:

### Classifications

| Classification | Meaning | Exit Code Impact |
|----------------|---------|------------------|
| `ACTIONABLE` | Must be addressed before merge | Causes exit code 1 |
| `NON_ACTIONABLE` | Informational, can be ignored | No impact |
| `AMBIGUOUS` | Needs human review | Included in output |

### Priority Levels

For actionable comments:

| Priority | Description |
|----------|-------------|
| `CRITICAL` | Must fix immediately - blocking issue |
| `MAJOR` | Must fix before merge - significant issue |
| `MINOR` | Should fix - notable but not blocking |
| `TRIVIAL` | Nice to fix - minor improvement |
| `UNKNOWN` | Could not determine priority |

## Supported Reviewers

Good To Go recognizes these automated reviewers:

### CodeRabbit

- Author: `coderabbitai[bot]`
- Detects: Critical, Major, Minor, Trivial severity markers
- Recognizes: Fingerprint comments, addressed markers, nitpicks

### Greptile

- Author: `greptile[bot]}` or signature in body
- Detects: Actionable comment patterns

### Claude Code

- Author: `claude-code[bot]` or signature
- Detects: "must", "should fix", "error", "bug" = actionable
- Detects: "consider", "suggestion", "might" = ambiguous
- Detects: "LGTM", "looks good" = non-actionable

### Cursor/Bugbot

- Author: `cursor[bot]`, `bugbot[bot]`
- Detects: Critical/High/Medium/Low severity

### Generic (Fallback)

- Used for unknown reviewers
- Marks resolved/outdated as non-actionable
- Everything else as ambiguous

## Caching

Good To Go caches API responses to reduce GitHub API calls:

- Cache location: `~/.goodtogo/cache.db`
- Default TTL: 5 minutes
- Use `--no-cache` to bypass

### Cache Security

- Cache file has 0600 permissions (owner read/write only)
- Cache directory has 0700 permissions
- No tokens stored in cache

## Error Handling

### Token Errors

```
Error: GITHUB_TOKEN environment variable not set
```

Set your token: `export GITHUB_TOKEN=ghp_...`

### Rate Limiting

```
Error: GitHub API rate limit exceeded
```

Wait for rate limit reset or use a token with higher limits.

### Invalid Repository

```
Error: Repository not found: owner/repo
```

Check repository name and token permissions.

## Python API

For programmatic use, import Good To Go directly:

```python
from goodtogo import PRAnalyzer, Container
from goodtogo.core.models import PRStatus

# Create container with dependencies
container = Container.create_default(github_token="ghp_...")

# Create analyzer
analyzer = PRAnalyzer(container)

# Analyze PR
result = analyzer.analyze("owner", "repo", 123)

# Check status
if result.status == PRStatus.READY:
    print("Ready to merge!")
elif result.status == PRStatus.ACTION_REQUIRED:
    print("Action required:")
    for comment in result.actionable_comments:
        print(f"  - [{comment.priority}] {comment.body[:50]}...")
elif result.status == PRStatus.CI_FAILING:
    print("CI failing:")
    for check in result.ci_status.checks:
        if check.status == "failure":
            print(f"  - {check.name}: {check.url}")
```

### Available Exports

```python
from goodtogo import (
    PRAnalyzer,      # Main analyzer class
    Container,       # Dependency injection container
    PRStatus,        # Status enum
    PRAnalysisResult,  # Result model
    Comment,         # Comment model
    CIStatus,        # CI status model
)
```
