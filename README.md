# Good To Go

**Deterministic PR readiness detection for AI coding agents**

Good To Go helps AI agents (like Claude Code) know exactly when a PR is ready to merge. No guessing, no polling indefinitely, no missing comments.

## The Problem

AI agents creating PRs face a common challenge: **How do I know when I'm actually done?**

- CI is still running... is it done yet?
- CodeRabbit left 12 comments... which ones need action?
- A reviewer requested changes... did I address them all?
- There are 3 unresolved threads... are they blocking?

Without deterministic answers, agents either wait too long, miss comments, or keep asking "is it ready yet?"

## The Solution

Good To Go provides **deterministic PR state analysis** via a simple CLI:

```bash
gtg 123 --repo owner/repo
```

Returns (default - AI-friendly):
- **Exit code 0**: Any analyzable state (ready, action required, threads, CI)
- **Exit code 4**: Error fetching data

For shell scripting, use `-q` for semantic exit codes without output, or `--semantic-codes` for output with semantic codes.

## Installation

```bash
pip install gtg
```

That's it. No other dependencies required.

## Usage

### Basic Check

```bash
# Check if PR #123 in myorg/myrepo is ready to merge
gtg 123 --repo myorg/myrepo

# With JSON output for programmatic use
gtg 123 --repo myorg/myrepo --format json

# Human-readable text format
gtg 123 --repo myorg/myrepo --format text
```

### Authentication

Set your GitHub token:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Note: The CLI reads `GITHUB_TOKEN` from the environment. There is no `--token` flag for security reasons.

### Exit Codes

**Default (AI-friendly)** - returns 0 for all analyzable states:

| Code | Meaning |
|------|---------|
| 0 | Any analyzable state (parse the JSON `status` field for details) |
| 4 | Error fetching PR data |

**With `-q` or `--semantic-codes`** - returns different codes per status:

| Code | Status | Meaning |
|------|--------|---------|
| 0 | READY | All clear - good to go! |
| 1 | ACTION_REQUIRED | Actionable comments need fixes |
| 2 | UNRESOLVED | Unresolved review threads |
| 3 | CI_FAILING | CI/CD checks failing |
| 4 | ERROR | Error fetching PR data |

Use `-q` (quiet mode) for shell scripts that only need the exit code.

### Quick Examples

Here's what the output looks like for each status (using `--format text`):

**READY** - All clear, ready to merge:
```
OK PR #123: READY
   CI: success (5/5 passed)
   Threads: 3/3 resolved
```

**ACTION_REQUIRED** - Actionable comments need attention:
```
!! PR #456: ACTION_REQUIRED
   CI: success (5/5 passed)
   Threads: 8/8 resolved

Action required:
   - Fix CRITICAL comment from coderabbit in src/db.py:42
   - 2 comments require investigation (ambiguous)
```

**UNRESOLVED_THREADS** - Review threads need resolution:
```
?? PR #789: UNRESOLVED_THREADS
   CI: success (5/5 passed)
   Threads: 2/4 resolved

Action required:
   - 2 unresolved review threads need attention
```

**CI_FAILING** - CI checks not passing:
```
XX PR #101: CI_FAILING
   CI: failure (3/5 passed)
   Threads: 2/2 resolved

Action required:
   - CI checks are failing - fix build/test errors
```

### Text Format Status Icons

| Icon | Status | Meaning |
|------|--------|---------|
| `OK` | READY | All clear - good to go! |
| `!!` | ACTION_REQUIRED | Actionable comments need fixes |
| `??` | UNRESOLVED_THREADS | Unresolved review threads |
| `XX` | CI_FAILING | CI/CD checks failing |
| `##` | ERROR | Error fetching PR data |

### JSON Output

```bash
gtg 123 --repo myorg/myrepo --format json
```

Returns structured data including:
- CI status (passed/failed/pending checks)
- Thread summary (resolved/unresolved counts)
- Classified comments (actionable vs non-actionable)
- Action items list

See [USAGE.md](USAGE.md) for full JSON schema and examples.

### GitHub Actions & Branch Protection

Make `gtg` a required check to block merging until PRs are truly ready:

```bash
# Enable branch protection with gtg-check as required
# Use actual job names from your CI workflow, not the workflow name
gh api repos/OWNER/REPO/branches/main/protection -X PUT --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Lint & Format", "Tests (3.9)", "Type Check", "gtg-check"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false
}
EOF
```

> **Note**: Use actual **job names** (e.g., `"Lint & Format"`) not workflow names (e.g., `"Tests & Quality"`).
> `enforce_admins: true` means admins must follow all rules. See [USAGE.md](USAGE.md#configuration-options) for details.

See [USAGE.md](USAGE.md#github-actions-integration) for the full GitHub Actions workflow setup.

## Supported Automated Reviewers

Good To Go recognizes and classifies comments from:

- **CodeRabbit** - Critical/Major/Minor/Trivial severity
- **Greptile** - Actionable comment detection
- **Claude Code** - Must/should/error/bug patterns
- **Cursor/Bugbot** - Severity-based classification
- **Generic** - Fallback for unknown reviewers

## For AI Agents

If you're an AI agent, use Good To Go in your PR workflow:

```python
import subprocess
import json

result = subprocess.run(
    ["gtg", "123", "--repo", "owner/repo", "--format", "json"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("Good to go! Ready to merge.")
elif result.returncode == 1:
    data = json.loads(result.stdout)
    print(f"Action required: {data['action_items']}")
```

Or use the Python API directly:

```python
from goodtogo import PRAnalyzer, Container

container = Container.create_default(github_token="ghp_...")
analyzer = PRAnalyzer(container)

result = analyzer.analyze("owner", "repo", 123)
if result.status == "READY":
    print("Good to go!")
else:
    for item in result.action_items:
        print(f"- {item}")
```

## Documentation

- [USAGE.md](USAGE.md) - Detailed CLI usage and examples
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development setup and contribution guide

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Created by [David Sifry](https://github.com/dsifry) with Claude Code.

---

**Made with Claude Code**
