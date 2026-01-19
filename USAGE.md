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
| `--repo`, `-r` | Repository in format `owner/repo` (auto-detected from git origin if omitted) |
| `--format` | Output format: `json` (default) or `text` |
| `--cache` | Cache backend: `sqlite` (default), `redis`, or `none` |
| `--cache-path` | SQLite cache path (default: `.goodtogo/cache.db`) |
| `--redis-url` | Redis URL (required if `--cache=redis`, or set `REDIS_URL` env var) |
| `--exclude-checks`, `-x` | CI check names to exclude (can be repeated, e.g., `-x slow-tests -x optional-lint`) |
| `--verbose`, `-v` | Show detailed output (includes ambiguous comments) |
| `-q`, `--quiet` | Quiet mode: no output, use semantic exit codes (like `grep -q`) |
| `--semantic-codes` | Use semantic exit codes (0=ready, 1=action, 2=threads, 3=ci, 4=error) |
| `--state-path` | SQLite state persistence path (default: `.goodtogo/state.db`) |
| `--refresh` | Force complete rescan, ignoring persisted state |
| `--version` | Show version number |

#### Examples

```bash
# Basic check (auto-detects repo from git origin)
gtg 123

# Explicit repo
gtg 123 --repo myorg/myrepo

# Human-readable text output
gtg 123 --format text

# Verbose output (shows ambiguous comments)
gtg 123 --format text --verbose

# Quiet mode for shell scripts (semantic exit codes, no output)
gtg 123 -q

# Semantic exit codes with output
gtg 123 --semantic-codes

# Exclude specific CI checks
gtg 123 --exclude-checks slow-tests --exclude-checks optional-lint
# Or short form
gtg 123 -x slow-tests -x optional-lint

# Disable caching
gtg 123 --cache none

# Use Redis cache
gtg 123 --cache redis --redis-url redis://localhost:6379

# Force rescan, ignoring persisted state
gtg 123 --refresh
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
| `??` | UNRESOLVED | Unresolved review threads |
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

**UNRESOLVED (Exit Code 2)** - Review threads need resolution:
```
?? PR #789: UNRESOLVED
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

- Author: `greptile[bot]`, `greptile-apps[bot]`, or signature in body
- Detects: Actionable comment patterns, severity markers

### Claude

- Author: `claude[bot]`, `claude-code[bot]`, `anthropic-claude[bot]`
- Body signature: Contains "Generated with Claude Code" or "Claude Code"
- Detects blocking patterns: "❌ Blocking", "🔴 Critical", "must fix before merge", "request changes"
- Detects approval patterns: "LGTM", "looks good", "ready to merge", "APPROVE", "✅ Overall"
- Detects suggestions: "consider", "suggestion", "might"
- Task completion summaries are marked as NON_ACTIONABLE

### Cursor/Bugbot

- Author: `cursor[bot]`, `cursor-bot`
- Body signature: Contains "cursor.com"
- Detects: Critical/High/Medium/Low severity
- PR-level summary comments are marked as NON_ACTIONABLE

### Generic (Fallback)

- Used for unknown reviewers
- Marks resolved/outdated as non-actionable
- Everything else as ambiguous

## Caching

Good To Go caches API responses to reduce GitHub API calls:

- Cache location: `.goodtogo/cache.db` (project-local)
- TTLs vary by data type:
  - PR metadata: 5 minutes
  - CI status (pending): 5 minutes
  - CI status (complete): 24 hours
  - Comments (NON_ACTIONABLE): 24 hours
  - Resolved threads: 24 hours
- Use `--cache none` to bypass caching

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

## GitHub Actions Integration

Good To Go integrates with GitHub Actions to automate PR readiness checks. This section covers setup from basic to advanced patterns.

### Quick Setup (AI Agent Instructions)

**For AI agents:** To set up GTG in a repository, follow these steps:

1. **Create the workflow file** at `.github/workflows/gtg.yml`
2. **Create or update a GitHub PAT** with `repo` scope (or use `GITHUB_TOKEN` for public repos)
3. **Add the secret** `GTG_PAT` to the repository (Settings → Secrets → Actions)
4. **Add branch protection** requiring the `Merge Ready (gtg)` check

Here's the complete workflow to create:

```yaml
name: PR Checks

on:
  pull_request:
    branches: [main]
  # Re-run GTG when reviews are submitted/dismissed (threads resolved)
  pull_request_review:
    types: [submitted, dismissed]

permissions:
  pull-requests: read
  contents: read
  checks: read
  statuses: read

jobs:
  # Your existing CI jobs go here (lint, test, build, etc.)
  # Example:
  # lint:
  #   runs-on: ubuntu-latest
  #   if: github.event_name == 'pull_request'
  #   steps:
  #     - uses: actions/checkout@v4
  #     - run: npm run lint

  # GTG merge readiness check - runs after CI jobs pass
  merge-ready:
    name: Merge Ready (gtg)
    runs-on: ubuntu-latest
    # List your CI jobs here so GTG runs after them
    # needs: [lint, test, build]
    if: |
      always() && (
        github.event_name == 'pull_request' ||
        github.event_name == 'pull_request_review'
      )
    timeout-minutes: 5

    steps:
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install gtg
        run: pip install gtg

      - name: Check PR readiness
        env:
          GITHUB_TOKEN: ${{ secrets.GTG_PAT }}
        run: |
          set -o pipefail
          echo "Checking PR #${{ github.event.pull_request.number }} readiness..."

          set +e
          gtg ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }} \
            --semantic-codes \
            --format text \
            --verbose \
            --exclude-checks "Merge Ready (gtg)" \
            --exclude-checks "claude" \
            --exclude-checks "CodeRabbit" 2>&1 | tee gtg-output.txt
          EXIT_CODE=${PIPESTATUS[0]}
          set -e

          echo "::group::GTG Check Details"
          cat gtg-output.txt
          echo "::endgroup::"

          case $EXIT_CODE in
            0)
              echo "::notice::PR #${{ github.event.pull_request.number }} is ready to merge"
              ;;
            1)
              echo "::error::PR has actionable comments that need to be addressed"
              exit 1
              ;;
            2)
              echo "::error::PR has unresolved review threads"
              exit 2
              ;;
            3)
              echo "::error::PR has failing CI checks"
              exit 3
              ;;
            4)
              echo "::error::Error fetching PR data from GitHub API"
              exit 4
              ;;
            *)
              echo "::error::GTG check failed with unexpected exit code: $EXIT_CODE"
              exit $EXIT_CODE
              ;;
          esac
```

### Understanding the Workflow

#### Dual Trigger Pattern

The workflow uses two triggers for optimal responsiveness:

```yaml
on:
  pull_request:
    branches: [main]
  pull_request_review:
    types: [submitted, dismissed]
```

| Trigger | When It Fires | What Runs |
|---------|---------------|-----------|
| `pull_request` | PR opened, updated, synchronized | Full CI + GTG |
| `pull_request_review` | Review submitted or dismissed | GTG only (CI skipped) |

This means when you resolve review threads, GTG re-runs immediately without waiting for CI to rebuild.

#### Excluding Checks

Always exclude GTG from its own evaluation to avoid circular dependencies:

```bash
--exclude-checks "Merge Ready (gtg)"
```

Also exclude AI reviewer checks that don't block merges:

```bash
--exclude-checks "claude" \
--exclude-checks "CodeRabbit" \
--exclude-checks "Cursor Bugbot"
```

#### Semantic Exit Codes

The workflow uses `--semantic-codes` for different handling per status:

| Exit Code | Status | Workflow Result |
|-----------|--------|-----------------|
| 0 | READY | ✅ Success |
| 1 | ACTION_REQUIRED | ❌ Failure |
| 2 | UNRESOLVED | ❌ Failure |
| 3 | CI_FAILING | ❌ Failure |
| 4 | ERROR | ❌ Failure |

### Advanced: Separate Workflow with `workflow_run`

For complex CI pipelines, run GTG in a separate workflow after CI completes:

```yaml
name: PR Readiness Check

on:
  workflow_run:
    workflows: ["Tests & Quality"]  # Your CI workflow name
    types: [completed]

permissions:
  actions: read
  checks: read
  contents: read
  pull-requests: read
  statuses: write

jobs:
  gtg-check:
    if: github.event.workflow_run.event == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - name: Get PR number
        id: pr
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          PR_NUMBER=$(gh api \
            repos/${{ github.repository }}/actions/runs/${{ github.event.workflow_run.id }} \
            --jq '.pull_requests[0].number')

          if [ -z "$PR_NUMBER" ] || [ "$PR_NUMBER" = "null" ]; then
            echo "Could not determine PR number from workflow run"
            exit 1
          fi

          echo "pr_number=$PR_NUMBER" >> $GITHUB_OUTPUT

      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.workflow_run.head_sha }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install gtg
        run: pip install gtg

      - name: Run gtg check
        id: gtg
        env:
          GITHUB_TOKEN: ${{ secrets.GTG_PAT }}
        run: |
          set +e
          gtg ${{ steps.pr.outputs.pr_number }} \
            --repo ${{ github.repository }} \
            --format json \
            --semantic-codes \
            --exclude-checks gtg-check > gtg-result.json
          EXIT_CODE=$?
          echo "exit_code=$EXIT_CODE" >> $GITHUB_OUTPUT

          # Write step summary
          STATUS=$(jq -r '.status' gtg-result.json)
          echo "## GTG Check Results" >> $GITHUB_STEP_SUMMARY
          echo "**PR #${{ steps.pr.outputs.pr_number }}**: $STATUS" >> $GITHUB_STEP_SUMMARY

          exit $EXIT_CODE

      - name: Post status to PR
        if: always()
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          EXIT_CODE="${{ steps.gtg.outputs.exit_code }}"

          case $EXIT_CODE in
            0) STATE="success"; DESC="✅ Good to Go!" ;;
            1) STATE="failure"; DESC="⚠️ Action Required" ;;
            2) STATE="failure"; DESC="💬 Unresolved Threads" ;;
            3) STATE="failure"; DESC="❌ CI Failing" ;;
            *) STATE="failure"; DESC="⚠️ Error" ;;
          esac

          gh api repos/${{ github.repository }}/statuses/${{ github.event.workflow_run.head_sha }} \
            -f state="$STATE" \
            -f target_url="${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}" \
            -f description="$DESC" \
            -f context="gtg-check"

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: gtg-results-pr-${{ steps.pr.outputs.pr_number }}
          path: gtg-result.json
```

### Advanced: Manual Re-run Workflow

Create a workflow for quick GTG re-checks without full CI:

```yaml
name: GTG Manual Re-run

on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: "PR number to check"
        required: true
        type: number

permissions:
  pull-requests: read
  contents: read
  checks: read
  statuses: read

jobs:
  gtg-check:
    name: Merge Ready (gtg)
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install gtg
        run: pip install gtg

      - name: Check PR readiness
        env:
          GITHUB_TOKEN: ${{ secrets.GTG_PAT }}
        run: |
          gtg ${{ github.event.inputs.pr_number }} \
            --repo ${{ github.repository }} \
            --semantic-codes \
            --format text \
            --verbose \
            --exclude-checks "Merge Ready (gtg)"
```

### Token Configuration

GTG needs a GitHub token with appropriate permissions.

#### Option 1: Personal Access Token (Recommended)

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Create a **Fine-grained token** with:
   - Repository access: Select your repositories
   - Permissions: `Pull requests: Read`, `Contents: Read`, `Checks: Read`
3. Or create a **Classic token** with `repo` scope
4. Add as repository secret named `GTG_PAT`

#### Option 2: Default GITHUB_TOKEN

For public repositories or basic checks, `GITHUB_TOKEN` works but has limitations:
- Cannot read some check run details
- Cannot access cross-repository data

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Key Configuration Points

| Configuration | Purpose |
|---------------|---------|
| `--semantic-codes` | Different exit codes per status (not just 0/non-zero) |
| `--exclude-checks` | Prevent circular dependency and ignore non-blocking checks |
| `--verbose` | Show ambiguous comments in output |
| `--format text` | Human-readable for logs; use `json` for parsing |
| `timeout-minutes: 5` | Prevent hung jobs |
| `set -o pipefail` | Catch errors in piped commands |

## Branch Protection

Make GTG a required check to prevent merging PRs that aren't ready.

### Quick Setup (AI Agent Instructions)

**For AI agents:** Run this command to enable branch protection with GTG:

```bash
gh api repos/OWNER/REPO/branches/main/protection -X PUT --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Merge Ready (gtg)"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false
}
EOF
```

Replace `OWNER/REPO` with the actual repository. Add other CI job names to `contexts` as needed.

### Using GitHub CLI

```bash
# Enable branch protection with all your CI checks + GTG
gh api repos/OWNER/REPO/branches/main/protection -X PUT --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint", "test", "build", "Merge Ready (gtg)"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false
}
EOF
```

> **Important**: Use the actual **job names** from your workflow, not the workflow name.
> For example, use `"Merge Ready (gtg)"` not `"PR Checks"`. You can find job names
> in the GitHub Actions UI or by running `gh pr checks <pr-number>`.

> **Note**: The defaults above provide maximum protection. See Configuration Options
> below for how to customize these settings.

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `required_status_checks.strict` | `true` | Require branches to be up to date before merging |
| `required_status_checks.contexts` | `["Merge Ready (gtg)"]` | Status checks that must pass |
| `enforce_admins` | `true` | **When `true`**: Admins must follow all rules (no bypass). **When `false`**: Admins can merge without passing checks, push directly to main, etc. |
| `allow_force_pushes` | `false` | **When `false`**: Force pushes to main are blocked for everyone. **When `true`**: Force pushes allowed (useful for rebasing, but can rewrite history). |

**Common customizations:**
- **Solo developer who needs flexibility**: Set `enforce_admins: false` to bypass checks when needed
- **Need to rebase/squash on main**: Set `allow_force_pushes: true` (only works if you're admin with `enforce_admins: false`)
- **Team environment**: Keep defaults (`enforce_admins: true`, `allow_force_pushes: false`) for maximum safety

### Using GitHub Web UI

1. Go to **Settings** > **Branches** > **Add branch protection rule**
2. Set **Branch name pattern** to `main`
3. Enable **Require status checks to pass before merging**
4. Search for and select `Merge Ready (gtg)` (and any other required checks)
5. Enable **Require branches to be up to date before merging**
6. Optionally disable **Include administrators** to allow admin bypass
7. Click **Create** or **Save changes**

### Verifying Protection

```bash
# Check current branch protection settings
gh api repos/OWNER/REPO/branches/main/protection
```

Example output (with recommended defaults):
```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint", "test", "Merge Ready (gtg)"]
  },
  "enforce_admins": {
    "enabled": true
  },
  "allow_force_pushes": {
    "enabled": false
  }
}
```

### What Gets Blocked

With `Merge Ready (gtg)` as a required status check:

| Status | Can Merge? |
|--------|------------|
| READY | ✅ Yes |
| ACTION_REQUIRED | ❌ No - fix comments first |
| UNRESOLVED | ❌ No - resolve threads first |
| CI_FAILING | ❌ No - fix CI first |
| ERROR | ❌ No - check failed |

This ensures PRs are only merged when:
- All CI checks are passing
- All actionable review comments are addressed
- All review threads are resolved

## Complete Setup Checklist (AI Agents)

Here's a complete checklist for AI agents setting up GTG in a new repository:

### 1. Create the Workflow File

Create `.github/workflows/gtg.yml` with the workflow from the [Quick Setup](#quick-setup-ai-agent-instructions) section above.

### 2. Configure Secrets

```bash
# Check if GTG_PAT secret exists
gh secret list --repo OWNER/REPO | grep GTG_PAT

# If not, the human needs to add it:
# 1. Go to https://github.com/settings/tokens
# 2. Create a Fine-grained or Classic token with repo access
# 3. Add as secret: gh secret set GTG_PAT --repo OWNER/REPO
```

### 3. Enable Branch Protection

```bash
# Enable branch protection requiring GTG
gh api repos/OWNER/REPO/branches/main/protection -X PUT --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Merge Ready (gtg)"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false
}
EOF
```

### 4. Verify Setup

```bash
# Create a test PR to verify the workflow runs
git checkout -b test/gtg-setup
echo "# Test" >> TEST.md
git add TEST.md
git commit -m "test: verify GTG workflow"
git push -u origin test/gtg-setup
gh pr create --title "test: verify GTG workflow" --body "Testing GTG setup"

# Watch the workflow
gh run watch

# Clean up
gh pr close --delete-branch
```

### 5. Customize Excludes

Edit the workflow to exclude any AI reviewer checks that shouldn't block merges:

```yaml
--exclude-checks "Merge Ready (gtg)" \
--exclude-checks "claude" \
--exclude-checks "CodeRabbit" \
--exclude-checks "Cursor Bugbot" \
--exclude-checks "greptile"
```
