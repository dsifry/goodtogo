# GoodToMerge

**Deterministic PR readiness detection for AI coding agents**

GoodToMerge helps AI agents (like Claude Code) know exactly when a PR is ready to merge. No guessing, no polling indefinitely, no missing comments.

## The Problem

AI agents creating PRs face a common challenge: **How do I know when I'm actually done?**

- CI is still running... is it done yet?
- CodeRabbit left 12 comments... which ones need action?
- A reviewer requested changes... did I address them all?
- There are 3 unresolved threads... are they blocking?

Without deterministic answers, agents either wait too long, miss comments, or keep asking "is it ready yet?"

## The Solution

GoodToMerge provides **deterministic PR state analysis** via a simple CLI:

```bash
gtm check owner/repo 123
```

Returns:
- **Exit code 0**: Ready to merge
- **Exit code 1**: Action required (actionable comments need fixes)
- **Exit code 2**: Unresolved threads exist
- **Exit code 3**: CI failing
- **Exit code 4**: Error fetching data

## Installation

```bash
pip install goodtomerge
```

That's it. No other dependencies required.

## Usage

### Basic Check

```bash
# Check if PR #123 in myorg/myrepo is ready to merge
gtm check myorg/myrepo 123

# With JSON output for programmatic use
gtm check myorg/myrepo 123 --json
```

### Authentication

Set your GitHub token:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Or pass it directly:

```bash
gtm check myorg/myrepo 123 --token ghp_your_token_here
```

### Exit Codes

| Code | Status | Meaning |
|------|--------|---------|
| 0 | READY | All clear - ready to merge |
| 1 | ACTION_REQUIRED | Actionable comments need fixes |
| 2 | UNRESOLVED | Unresolved review threads |
| 3 | CI_FAILING | CI/CD checks failing |
| 4 | ERROR | Error fetching PR data |

### JSON Output

```bash
gtm check myorg/myrepo 123 --json
```

Returns structured data including:
- CI status (passed/failed/pending checks)
- Thread summary (resolved/unresolved counts)
- Classified comments (actionable vs non-actionable)
- Action items list

## Supported Automated Reviewers

GoodToMerge recognizes and classifies comments from:

- **CodeRabbit** - Critical/Major/Minor/Trivial severity
- **Greptile** - Actionable comment detection
- **Claude Code** - Must/should/error/bug patterns
- **Cursor/Bugbot** - Severity-based classification
- **Generic** - Fallback for unknown reviewers

## For AI Agents

If you're an AI agent, use GoodToMerge in your PR workflow:

```python
import subprocess
import json

result = subprocess.run(
    ["gtm", "check", "owner/repo", "123", "--json"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("PR is ready to merge!")
elif result.returncode == 1:
    data = json.loads(result.stdout)
    print(f"Action required: {data['action_items']}")
```

Or use the Python API directly:

```python
from goodtomerge import PRAnalyzer, Container

container = Container.create_default(github_token="ghp_...")
analyzer = PRAnalyzer(container)

result = analyzer.analyze("owner", "repo", 123)
if result.status == "READY":
    print("Ready to merge!")
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
