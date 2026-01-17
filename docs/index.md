---
layout: default
title: Good To Go
description: Deterministic PR readiness detection for AI coding agents
---

# Good To Go

**The missing piece in AI-assisted development: knowing when you're actually done.**

---

## The Problem No One Talks About

AI coding agents are transforming software development. They can write code, fix bugs, respond to review comments, and create pull requests. But they all share one fundamental problem:

**They can't reliably know when a PR is ready to merge.**

Think about it. When you ask an AI agent to "fix the CI and address the review comments," how does it know when it's finished?

- CI is running... is it done yet? Let me check again. And again.
- CodeRabbit left 12 comments... which ones actually need fixes vs. which are just suggestions?
- A reviewer wrote "consider using X"... is that blocking or just a thought?
- There are unresolved threads... but the code was already fixed in the last commit.

Without deterministic answers, agents either:
- **Poll indefinitely** - checking CI status in a loop, burning tokens
- **Give up too early** - "I've pushed my changes" (but CI is failing)
- **Miss actionable feedback** - buried in a sea of informational comments
- **Ask you constantly** - "Is it ready now? How about now?"

## The Solution: Deterministic PR Analysis

Good To Go provides a single command that answers the question definitively:

```bash
gtg 123
```

That's it. One command. One answer.

| Status | Meaning | What to Do |
|--------|---------|------------|
| `READY` | All clear | Merge it |
| `ACTION_REQUIRED` | Comments need fixes | Address them |
| `UNRESOLVED_THREADS` | Open discussions | Resolve them |
| `CI_FAILING` | Checks not passing | Fix the build |

No ambiguity. No guessing. No infinite loops.

## How It Works

Good To Go analyzes your PR across three dimensions:

### 1. CI Status Aggregation
Combines all GitHub check runs and commit statuses into a single pass/fail/pending state. Handles the complexity of multiple CI systems, required vs optional checks, and in-progress runs.

### 2. Intelligent Comment Classification
Not all review comments are created equal. Good To Go classifies each comment as:

- **ACTIONABLE** - Must fix before merge (blocking issues, critical bugs)
- **NON_ACTIONABLE** - Safe to ignore (praise, nitpicks, resolved items)
- **AMBIGUOUS** - Needs human judgment (suggestions, questions)

Built-in parsers understand the patterns of popular automated reviewers:
- **CodeRabbit** - Severity indicators (Critical/Major/Minor/Trivial)
- **Greptile** - Code analysis findings
- **Claude** - Blocking markers and approval patterns
- **Cursor/Bugbot** - Bug severity levels

### 3. Thread Resolution Tracking
Distinguishes between truly unresolved discussions and threads that are technically "unresolved" but already addressed in subsequent commits.

## Designed for AI Agents

Good To Go is built specifically for how AI agents work:

### Exit Codes That Make Sense
Default mode returns `0` for any analyzable state—because AI agents should parse the JSON output, not interpret exit codes as errors.

```bash
# AI-friendly (default): exit 0 + parse JSON
gtg 123 --format json

# Shell-script friendly: semantic exit codes
gtg 123 -q  # quiet mode, exit code only
```

### Structured Output
Every response includes exactly what an agent needs to take action:

```json
{
  "status": "ACTION_REQUIRED",
  "action_items": [
    "Fix CRITICAL comment from coderabbit in src/db.py:42",
    "Resolve thread started by @reviewer in api.py"
  ],
  "actionable_comments": [...],
  "ci_status": {...},
  "threads": {...}
}
```

### State Persistence
Track what's already been handled across agent sessions:

```bash
gtg 123 --state-path .goodtogo/state.db  # Remember dismissed comments
gtg 123 --refresh                         # Force fresh analysis
```

## Use Cases

### As a CI Gate
Make `gtg` a required status check. PRs can't merge until they're truly ready—not just "CI passed."

```yaml
# .github/workflows/pr-check.yml
- name: Check PR readiness
  run: gtg ${{ github.event.pull_request.number }} --semantic-codes
```

### In Agent Workflows
Give your AI agent a definitive answer instead of endless polling:

```python
result = subprocess.run(["gtg", pr_number, "--format", "json"], ...)
data = json.loads(result.stdout)

if data["status"] == "READY":
    merge_pr()
elif data["status"] == "ACTION_REQUIRED":
    for item in data["action_items"]:
        address_feedback(item)
```

### For PR Shepherding
Monitor a PR through its entire lifecycle:

```bash
while true; do
  gtg 123 -q
  case $? in
    0) echo "Ready to merge!"; break ;;
    1) handle_comments ;;
    2) resolve_threads ;;
    3) wait_for_ci ;;
  esac
  sleep 60
done
```

## Quick Start

```bash
# Install
pip install gtg

# Set your GitHub token
export GITHUB_TOKEN=ghp_...

# Check a PR (auto-detects repo from git origin)
gtg 123

# Explicit repo
gtg 123 --repo owner/repo

# Human-readable output
gtg 123 --format text
```

## Philosophy

Good To Go embeds several opinions about PR workflows:

1. **Determinism over heuristics** - Every PR has exactly one status at any moment
2. **Actionability over completeness** - Surface what needs action, not everything
3. **Agent-first design** - Structured output, sensible defaults, state persistence
4. **Fail open for ambiguity** - When uncertain, flag for human review rather than block

## Links

- [GitHub Repository](https://github.com/dsifry/goodtogo)
- [PyPI Package](https://pypi.org/project/gtg/)
- [Full Documentation](https://github.com/dsifry/goodtogo/blob/main/USAGE.md)
- [Contributing Guide](https://github.com/dsifry/goodtogo/blob/main/CONTRIBUTING.md)

---

<p align="center">
  <strong>Made with Claude Code</strong><br>
  <em>by <a href="https://github.com/dsifry">David Sifry</a></em>
</p>
