# Good To Go

[![PyPI version](https://badge.fury.io/py/gtg.svg)](https://badge.fury.io/py/gtg)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/dsifry/goodtogo)

**Deterministic PR readiness detection for AI coding agents**

> *"Is the PR ready to merge?"* — Finally, a definitive answer.

[Documentation](https://dsifry.github.io/goodtogo/) · [PyPI](https://pypi.org/project/gtg/) · [Contributing](CONTRIBUTING.md)

---

## Why Good To Go?

AI agents can write code, fix bugs, and respond to reviews. But they all struggle with one question: **"Am I done yet?"**

- CI is running... check again... still running...
- CodeRabbit left 12 comments — which ones are blocking?
- Reviewer wrote "consider X" — is that a request or a suggestion?
- Threads are unresolved — but the fix is already pushed

**Good To Go answers this definitively:**

```bash
gtg 123
```

```
OK PR #123: READY
   CI: success (5/5 passed)
   Threads: 3/3 resolved
```

One command. One status. No guessing.

## How It Works

```mermaid
flowchart LR
    PR[Pull Request] --> GTG[gtg]
    GTG --> CI[CI Status]
    GTG --> Comments[Comment Analysis]
    GTG --> Threads[Thread Resolution]

    CI --> Status{Status}
    Comments --> Status
    Threads --> Status

    Status --> READY[✓ READY]
    Status --> ACTION[! ACTION_REQUIRED]
    Status --> UNRESOLVED[? UNRESOLVED_THREADS]
    Status --> FAILING[✗ CI_FAILING]
```

Good To Go combines three analyses:

| Analysis | What It Does |
|----------|--------------|
| **CI Status** | Aggregates all checks into pass/fail/pending |
| **Comment Classification** | Identifies actionable vs. informational comments |
| **Thread Resolution** | Tracks which discussions are truly blocking |

### Intelligent Comment Classification

Not all comments need action. Good To Go classifies each one:

| Classification | Examples | Action |
|---------------|----------|--------|
| **ACTIONABLE** | "Critical: SQL injection vulnerability" | Must fix |
| **NON_ACTIONABLE** | "LGTM!", nitpicks, resolved items | Ignore |
| **AMBIGUOUS** | "Consider using X", questions | Human review |

Built-in support for: **CodeRabbit**, **Greptile**, **Claude**, **Cursor/Bugbot**

## Quick Start

```bash
# Install
pip install gtg

# Set GitHub token
export GITHUB_TOKEN=ghp_...

# Check a PR (auto-detects repo)
gtg 123

# Explicit repo
gtg 123 --repo owner/repo
```

## Output Formats

### Text (Human-Readable)

```bash
gtg 123 --format text
```

```
!! PR #456: ACTION_REQUIRED
   CI: success (5/5 passed)
   Threads: 8/8 resolved

Action required:
   - Fix CRITICAL comment from coderabbit in src/db.py:42
```

### JSON (For Agents)

```bash
gtg 123 --format json
```

```json
{
  "status": "ACTION_REQUIRED",
  "action_items": ["Fix CRITICAL comment from coderabbit in src/db.py:42"],
  "actionable_comments": [...],
  "ci_status": {"state": "success", "passed": 5, "total_checks": 5}
}
```

## Exit Codes

**Default (AI-friendly)** — parse the JSON for details:

| Code | Meaning |
|------|---------|
| 0 | Any analyzable state |
| 4 | Error |

**With `-q` or `--semantic-codes`** — for shell scripts:

| Code | Status |
|------|--------|
| 0 | READY |
| 1 | ACTION_REQUIRED |
| 2 | UNRESOLVED_THREADS |
| 3 | CI_FAILING |
| 4 | ERROR |

## Use as CI Gate

Make `gtg` a required check to block merges until PRs are truly ready:

```yaml
# .github/workflows/pr-check.yml
- name: Check PR readiness
  run: gtg ${{ github.event.pull_request.number }} --semantic-codes
```

See [USAGE.md](USAGE.md#github-actions-integration) for full workflow setup.

## For AI Agents

```python
import subprocess
import json

result = subprocess.run(
    ["gtg", "123", "--format", "json"],
    capture_output=True, text=True
)
data = json.loads(result.stdout)

if data["status"] == "READY":
    print("Merge it!")
else:
    for item in data["action_items"]:
        print(f"TODO: {item}")
```

Or use the Python API:

```python
from goodtogo import PRAnalyzer, Container

container = Container.create_default(github_token="ghp_...")
analyzer = PRAnalyzer(container)
result = analyzer.analyze("owner", "repo", 123)
```

## State Persistence

Track handled comments across sessions:

```bash
gtg 123 --state-path .goodtogo/state.db  # Remember dismissed comments
gtg 123 --refresh                         # Force fresh analysis
```

## Documentation

- **[Landing Page](https://dsifry.github.io/goodtogo/)** — Philosophy and vision
- **[USAGE.md](USAGE.md)** — Complete CLI reference
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Development guide

## License

MIT License — see [LICENSE](LICENSE)

---

<p align="center">
  <strong>Made with Claude Code</strong><br>
  <em>by <a href="https://github.com/dsifry">David Sifry</a></em>
</p>
