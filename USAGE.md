# Good To Go Usage Guide

Complete documentation for the `gtg` CLI tool.

## Installation

```bash
pip install gtg
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

### Environment Variable (Required)

```bash
export GITHUB_TOKEN=ghp_your_token_here
gtg 123 --repo owner/repo
```

Note: The CLI reads `GITHUB_TOKEN` from the environment. There is no `--token` flag for security reasons.

### Creating a Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select the `repo` scope
4. Copy the token and set it as `GITHUB_TOKEN`

## Commands

### `gtg`

Check if a PR is ready to merge.

```bash
gtg <pr_number> --repo <owner/repo> [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `pr_number` | Pull request number |

#### Options

| Option | Description |
|--------|-------------|
| `--repo`, `-r` | Repository in format `owner/repo` (e.g., `facebook/react`) - **required** |
| `--format` | Output format: `json` (default) or `text` |
| `--cache` | Cache backend: `sqlite` (default), `redis`, or `none` |
| `--cache-path` | SQLite cache path (default: `.goodtogo/cache.db`) |
| `--redis-url` | Redis URL (required if `--cache=redis`, or set `REDIS_URL` env var) |
| `--verbose`, `-v` | Show detailed output (includes ambiguous comments) |
| `-q`, `--quiet` | Quiet mode: no output, use semantic exit codes (like `grep -q`) |
| `--semantic-codes` | Use semantic exit codes (0=ready, 1=action, 2=threads, 3=ci, 4=error) |
| `--version` | Show version number |

#### Examples

```bash
# Basic check (JSON output by default, AI-friendly exit codes)
gtg 123 --repo myorg/myrepo

# Human-readable text output
gtg 123 --repo myorg/myrepo --format text

# Verbose output (shows ambiguous comments)
gtg 123 --repo myorg/myrepo --format text --verbose

# Quiet mode for shell scripts (semantic exit codes, no output)
gtg 123 --repo myorg/myrepo -q

# Semantic exit codes with output
gtg 123 --repo myorg/myrepo --semantic-codes

# Disable caching
gtg 123 --repo myorg/myrepo --cache none

# Use Redis cache
gtg 123 --repo myorg/myrepo --cache redis --redis-url redis://localhost:6379
```

## Exit Codes

Good To Go supports two exit code modes:

### Default Mode (AI-friendly)

By default, gtg returns 0 for any analyzable state. This is optimized for AI agents that interpret non-zero exit codes as errors:

| Code | Description |
|------|-------------|
| 0 | Any analyzable state (READY, ACTION_REQUIRED, UNRESOLVED, CI_FAILING) |
| 4 | Error fetching data |

Parse the JSON `status` field to determine the actual PR state.

### Semantic Mode (`-q` or `--semantic-codes`)

For shell scripts that need different exit codes per status:

| Code | Status | Description |
|------|--------|-------------|
| 0 | `READY` | PR is ready to merge |
| 1 | `ACTION_REQUIRED` | Actionable comments exist |
| 2 | `UNRESOLVED` | Unresolved review threads |
| 3 | `CI_FAILING` | CI checks failing/pending |
| 4 | `ERROR` | Error fetching data |

Use `-q` for quiet mode (semantic codes, no output) or `--semantic-codes` for semantic codes with output.

### Using Exit Codes in Scripts

```bash
# For shell scripts that need semantic exit codes, use -q (quiet mode)
gtg 123 --repo owner/repo -q
case $? in
  0) echo "Ready to merge!" ;;
  1) echo "Comments need attention" ;;
  2) echo "Threads need resolution" ;;
  3) echo "CI not passing" ;;
  4) echo "Error occurred" ;;
esac

# Or use --semantic-codes if you also want the output
gtg 123 --repo owner/repo --semantic-codes --format text
```

## Text Output Format

With `--format text`, Good To Go outputs human-readable status information:

```bash
gtg 123 --repo myorg/myrepo --format text
```

### Status Icons

| Icon | Status | Meaning |
|------|--------|---------|
| `OK` | READY | All clear - good to go! |
| `!!` | ACTION_REQUIRED | Actionable comments need fixes |
| `??` | UNRESOLVED_THREADS | Unresolved review threads |
| `XX` | CI_FAILING | CI/CD checks failing |
| `##` | ERROR | Error fetching PR data |

### Example Output by Status

**READY (Exit Code 0)** - All clear, ready to merge:
```
OK PR #123: READY
   CI: success (5/5 passed)
   Threads: 3/3 resolved
```

**ACTION_REQUIRED (Exit Code 1)** - Actionable comments need attention:
```
!! PR #456: ACTION_REQUIRED
   CI: success (5/5 passed)
   Threads: 8/8 resolved

Action required:
   - Fix CRITICAL comment from coderabbit in src/db.py:42
   - 2 comments require investigation (ambiguous)
```

**UNRESOLVED_THREADS (Exit Code 2)** - Review threads need resolution:
```
?? PR #789: UNRESOLVED_THREADS
   CI: success (5/5 passed)
   Threads: 2/4 resolved

Action required:
   - 2 unresolved review threads need attention
```

**CI_FAILING (Exit Code 3)** - CI checks not passing:
```
XX PR #101: CI_FAILING
   CI: failure (3/5 passed)
   Threads: 2/2 resolved

Action required:
   - CI checks are failing - fix build/test errors
```

**CI_PENDING** - CI still running:
```
XX PR #202: CI_FAILING
   CI: pending (8/12 passed)
   Threads: 2/2 resolved

Action required:
   - CI checks are still running - wait for completion
```

### Verbose Output

With `--verbose`, the text output also shows ambiguous comments that may need investigation:

```bash
gtg 123 --repo myorg/myrepo --format text --verbose
```

```
!! PR #123: ACTION_REQUIRED
   CI: success (5/5 passed)
   Threads: 8/8 resolved

Action required:
   - Fix CRITICAL comment from coderabbit in src/db.py:42

Ambiguous (needs investigation):
   - [coderabbitai[bot]] Consider using a connection pool for better performance...
   - [greptile[bot]] This pattern might cause issues in high-concurrency scenarios...
```

## JSON Output Format

With `--format json`, Good To Go outputs structured data:

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
