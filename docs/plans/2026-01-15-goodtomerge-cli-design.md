# Good To Go CLI Design Specification

**Version**: 0.1.0
**Date**: 2026-01-15
**Status**: Draft - Pending Review

## Overview

Good To Go is a deterministic PR readiness detection library and CLI for AI coding agents. It answers the question: "Is this PR ready to merge?" without requiring AI inference, polling indefinitely, or missing comments.

## Problem Statement

AI agents creating PRs face a common challenge: **How do I know when I'm actually done?**

- CI is still running... is it done yet?
- CodeRabbit left 12 comments... which ones need action?
- A reviewer requested changes... did I address them all?
- There are 3 unresolved threads... are they blocking?

Without deterministic answers, agents either wait too long, miss comments, or keep asking "is it ready yet?"

## Solution

A Python library (with thin CLI wrapper) that:

1. Fetches PR state from GitHub API (CI status, comments, threads)
2. Identifies automated reviewers (CodeRabbit, Greptile, Claude Code, Cursor/Bugbot)
3. Classifies comments as ACTIONABLE, NON_ACTIONABLE, or AMBIGUOUS using rule-based parsing
4. Returns deterministic status with structured JSON output

**Key constraint**: No internal AI calls. Pure rule-based, deterministic parsing for speed and cost.

## User Personas

### Primary: Orchestrated AI Agent

**WHO**: An AI coding agent (Claude Code, Cursor, Copilot) operating as part of an automated swarm or orchestration pipeline.

**CONTEXT**: The agent has created a PR, addressed initial feedback, and pushed commits. It needs to determine whether to:
- Proceed to merge (all clear)
- Iterate on feedback (actionable items remain)
- Wait for human input (ambiguous situation)
- Escalate (persistent failures)

**NEEDS**:
- Machine-parseable JSON output for programmatic decision-making
- Deterministic exit codes for pipeline control flow
- Zero ambiguity - every comment classified
- Fast response time (< 2s) to avoid blocking pipelines
- No false negatives (never miss actionable feedback)

**SUCCESS**: Agent autonomously determines next action without human intervention in 95%+ of cases.

### Secondary: Human Orchestrating AI Agent

**WHO**: A developer or DevOps engineer manually supervising an AI agent's PR workflow.

**CONTEXT**: The human has asked an AI agent to create a PR and wants reassurance that all review feedback has been properly addressed before approving merge.

**NEEDS**:
- Confidence that nothing was missed
- Quick verification without manually checking GitHub UI
- Clear summary of what was addressed vs. what needs attention
- Ability to drill into ambiguous items

**SUCCESS**: Human can confidently approve merge knowing all comments/threads are resolved.

## Use Cases

### UC-1: Agent Determines PR Ready to Merge

**WHO**: Orchestrated AI Agent
**WANTS**: To know if PR is ready for merge
**SO THAT**: It can proceed to merge or move to next task
**WHEN**: After pushing commits that address review feedback

**Flow**:
```
1. Agent calls: analyzer.analyze(owner, repo, pr_number)
2. Good To Go fetches CI status, comments, threads
3. All CI checks pass, no actionable comments, all threads resolved
4. Returns: PRStatus.READY (exit code 0)
5. Agent proceeds to merge
```

**Acceptance Criteria**:
- Exit code 0 returned only when ALL conditions met
- JSON output includes empty `actionable_comments` list
- `needs_action: false` in response

---

### UC-2: Agent Identifies Actionable Feedback

**WHO**: Orchestrated AI Agent
**WANTS**: To identify which comments require action
**SO THAT**: It can address them systematically
**WHEN**: Automated reviewers (CodeRabbit, Greptile) have posted feedback

**Flow**:
```
1. Agent calls: analyzer.analyze(owner, repo, pr_number)
2. Good To Go parses CodeRabbit comments, finds 3 with 🟡 Minor severity
3. Returns: PRStatus.ACTION_REQUIRED (exit code 1)
4. Response includes actionable_comments with file paths and line numbers
5. Agent iterates through comments and addresses each
```

**Acceptance Criteria**:
- Each actionable comment includes `file_path`, `line_number`, `priority`
- Comments sorted by priority (CRITICAL → TRIVIAL)
- `action_items` list provides human-readable summary

---

### UC-3: Agent Handles Ambiguous Comments

**WHO**: Orchestrated AI Agent
**WANTS**: To know when human judgment is needed
**SO THAT**: It can escalate appropriately rather than guess
**WHEN**: A comment doesn't match known reviewer patterns

**Flow**:
```
1. Agent calls: analyzer.analyze(owner, repo, pr_number)
2. Good To Go finds human comment: "This might need refactoring"
3. Cannot determine if blocking → AMBIGUOUS classification
4. Returns: PRStatus.ACTION_REQUIRED with requires_investigation=True
5. Agent escalates to human or treats as potentially blocking
```

**Acceptance Criteria**:
- AMBIGUOUS comments have `requires_investigation: true`
- Never silently skip ambiguous comments
- `ambiguous_comments` list populated separately for easy filtering

---

### UC-4: Agent Waits for CI Completion

**WHO**: Orchestrated AI Agent
**WANTS**: To know if CI is still running
**SO THAT**: It can wait or proceed appropriately
**WHEN**: PR was just pushed and checks are in progress

**Flow**:
```
1. Agent calls: analyzer.analyze(owner, repo, pr_number)
2. Good To Go fetches CI status, finds 2/5 checks still pending
3. Returns: PRStatus.CI_FAILING (exit code 3) with ci_status.pending > 0
4. Agent waits and retries after interval
```

**Acceptance Criteria**:
- `ci_status.pending` count accurate
- `ci_status.state` = "pending" when any check incomplete
- Individual check details in `ci_status.checks` list

---

### UC-5: Human Verifies All Feedback Addressed

**WHO**: Human orchestrating AI agent
**WANTS**: Confidence that PR is truly ready
**SO THAT**: They can approve merge without manually checking GitHub
**WHEN**: AI agent reports PR is ready

**Flow**:
```
1. Human runs: gtm check 123 --repo org/repo --format text
2. Good To Go displays summary:
   ✅ PR #123: READY
   CI: success (5/5 passed)
   Threads: 8/8 resolved
   Actionable comments: 0
3. Human sees clear confirmation, approves merge
```

**Acceptance Criteria**:
- Text output provides human-readable summary
- All resolved threads counted accurately
- No false sense of security (ambiguous items flagged)

---

### UC-6: Agent Handles Outside-Diff-Range Comments

**WHO**: Orchestrated AI Agent
**WANTS**: To catch feedback in review bodies, not just inline comments
**SO THAT**: Important feedback isn't missed due to GitHub's placement
**WHEN**: CodeRabbit posts "Outside diff range" comments in review body

**Flow**:
```
1. Agent calls: analyzer.analyze(owner, repo, pr_number)
2. Good To Go parses review bodies, finds "Outside diff range" section
3. Extracts file paths and line numbers from review body text
4. Classifies as ACTIONABLE with MINOR priority
5. Agent addresses these alongside inline comments
```

**Acceptance Criteria**:
- Review body content parsed, not just inline comments
- "Outside diff range" pattern detected
- File paths extracted from markdown in review body

---

### UC-7: Multi-Reviewer Scenario

**WHO**: Orchestrated AI Agent
**WANTS**: To aggregate feedback from multiple automated reviewers
**SO THAT**: All reviewer feedback is considered holistically
**WHEN**: PR has CodeRabbit, Greptile, and human reviews

**Flow**:
```
1. Agent calls: analyzer.analyze(owner, repo, pr_number)
2. Good To Go identifies 3 reviewers: CodeRabbit, Greptile, human
3. Parses each with appropriate parser (CodeRabbit → CodeRabbitParser, etc.)
4. Aggregates: 2 CodeRabbit actionable, 1 Greptile actionable, 1 human ambiguous
5. Returns unified response with all comments tagged by reviewer_type
```

**Acceptance Criteria**:
- Each comment tagged with `reviewer_type`
- Different parsers used per reviewer
- Unified `actionable_comments` list across all reviewers

## MVP Scope (v0.1)

### MUST Have (v0.1 Release)

| Feature | Rationale |
|---------|-----------|
| JSON output (default) | Primary user is AI agent |
| Exit codes 0-4 | Pipeline integration |
| CodeRabbit parser | Most common automated reviewer |
| Greptile parser | Used in target workflows |
| Generic parser (fallback) | Handle unknown reviewers |
| SQLite cache | Zero-config local caching |
| GitHub REST/GraphQL API | Fetch PR state |
| Thread resolution tracking | Core requirement |
| AMBIGUOUS classification | Never skip unknown comments |

### SHOULD Have (v0.1 if time permits)

| Feature | Rationale |
|---------|-----------|
| Text output (`--format text`) | Secondary user convenience |
| Claude Code parser | Growing adoption |
| Cursor/Bugbot parser | Growing adoption |
| Redis cache option | Team/CI scenarios |
| `--verbose` flag | Debugging support |

### COULD Have (v0.2+)

| Feature | Rationale |
|---------|-----------|
| Webhook listener | Push notifications vs polling |
| GitHub App auth | Better than PAT for teams |
| Custom parser plugins | Extensibility |
| `--watch` mode | Continuous monitoring |

### WON'T Have (Out of Scope)

| Feature | Rationale |
|---------|-----------|
| GitLab/Bitbucket support | GitHub-first for v1 |
| AI-based classification | Violates deterministic constraint |
| Web UI | CLI/library focus |
| Slack/Discord notifications | External integration |

## User Journey

### AI Agent Swarm Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PR SHEPHERD ORCHESTRATION                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. AGENT CREATES PR                                                  │
│    - Implements feature/fix                                          │
│    - Pushes to branch                                                │
│    - Creates PR via GitHub API                                       │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. AUTOMATED REVIEWERS RUN                                           │
│    - CodeRabbit analyzes diff                                        │
│    - Greptile posts review                                           │
│    - CI/CD checks execute                                            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. AGENT CALLS GOODTOMERGE                                           │
│                                                                      │
│    result = analyzer.analyze(owner, repo, pr_number)                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌───────────┐  ┌───────────┐  ┌───────────┐
            │  READY    │  │  ACTION   │  │ AMBIGUOUS │
            │ (exit 0)  │  │ REQUIRED  │  │  ITEMS    │
            │           │  │ (exit 1)  │  │           │
            └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
                  │              │              │
                  ▼              ▼              ▼
            ┌───────────┐  ┌───────────┐  ┌───────────┐
            │  MERGE    │  │  ITERATE  │  │ ESCALATE  │
            │    PR     │  │ Address   │  │ to human  │
            │           │  │ comments  │  │           │
            └───────────┘  └─────┬─────┘  └───────────┘
                                 │
                                 │ (loop back)
                                 ▼
                    ┌─────────────────────────┐
                    │ 3. AGENT CALLS          │
                    │    GOODTOMERGE (again)  │
                    └─────────────────────────┘
```

### Decision Tree

```
START: analyzer.analyze(owner, repo, pr_number)
  │
  ├─► CI checks pending?
  │     YES → return CI_FAILING (exit 3), wait and retry
  │
  ├─► CI checks failed?
  │     YES → return CI_FAILING (exit 3), fix failures
  │
  ├─► Unresolved threads exist?
  │     YES → return UNRESOLVED_THREADS (exit 2), resolve threads
  │
  ├─► Actionable comments exist?
  │     YES → return ACTION_REQUIRED (exit 1), address comments
  │
  ├─► Ambiguous comments exist?
  │     YES → return ACTION_REQUIRED (exit 1) with requires_investigation
  │           Agent decides: address or escalate to human
  │
  └─► All clear
        return READY (exit 0), proceed to merge
```

## Security Requirements

### Input Validation

All external inputs MUST be validated before use:

```python
import re

# GitHub identifier pattern: alphanumeric, dots, hyphens, underscores
# Must start and end with alphanumeric
GITHUB_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]{0,37}[a-zA-Z0-9])?$')

def validate_github_identifier(value: str, field_name: str) -> str:
    """
    Validate GitHub owner/repo name format.

    Raises:
        ValueError: If validation fails
    """
    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    if len(value) > 39:  # GitHub max length
        raise ValueError(f"{field_name} exceeds maximum length (39 chars)")

    if not GITHUB_ID_PATTERN.match(value):
        raise ValueError(
            f"{field_name} contains invalid characters. "
            "Must be alphanumeric with ._- allowed, "
            "starting and ending with alphanumeric."
        )

    return value

def validate_pr_number(value: int) -> int:
    """Validate PR number is positive integer."""
    if value <= 0:
        raise ValueError("PR number must be positive")
    if value > 2147483647:  # Max int32
        raise ValueError("PR number exceeds maximum value")
    return value
```

**Validation points:**
- CLI argument parsing (Click validates int for PR number)
- `Container.create_default()` validates owner/repo before use
- Cache key construction uses validated inputs only
- GitHub API calls use validated inputs only

### Token Security

GitHub tokens MUST be protected:

```python
class GitHubAdapter:
    """GitHub API adapter with secure token handling."""

    def __init__(self, token: str):
        # Token stored in private attribute
        self._token = token
        # Never log, cache, or serialize the token

    def __repr__(self) -> str:
        # Prevent token leakage in logs/debug output
        return "GitHubAdapter(token=<redacted>)"

    def __str__(self) -> str:
        return self.__repr__()
```

**Token handling rules:**
1. Token read from `GITHUB_TOKEN` environment variable only
2. Token stored in private `_token` attribute
3. Token NEVER appears in:
   - Log messages
   - Cache keys or values
   - Error messages
   - Exception tracebacks (use redaction)
   - `__repr__` or `__str__` output
4. Token NEVER serialized to JSON or persisted

### SQLite Cache Security

SQLite cache file MUST have restricted permissions:

```python
import os
import stat

def create_cache_directory(path: str) -> None:
    """Create cache directory with secure permissions."""
    cache_dir = os.path.dirname(path)

    if cache_dir and not os.path.exists(cache_dir):
        # Create directory with 0700 (owner read/write/execute only)
        os.makedirs(cache_dir, mode=0o700, exist_ok=True)

def secure_cache_file(path: str) -> None:
    """Ensure cache file has restricted permissions."""
    if os.path.exists(path):
        # Set file permissions to 0600 (owner read/write only)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
```

**File permission rules:**
- Cache directory: `0700` (owner only)
- Cache database file: `0600` (owner read/write only)
- Permissions set on creation and verified on open
- Warning logged if permissions are too permissive

### Cache Key Sanitization

Cache keys MUST be constructed safely:

```python
def build_cache_key(*parts: str) -> str:
    """
    Build cache key from validated parts.

    All parts must be pre-validated via validate_github_identifier()
    or validate_pr_number() before calling this function.
    """
    # Double-check no special characters that could cause issues
    for part in parts:
        if ':' in str(part) or '*' in str(part) or '?' in str(part):
            raise ValueError(f"Invalid character in cache key part: {part}")

    return ':'.join(str(p) for p in parts)

# Usage:
# key = build_cache_key("pr", owner, repo, str(pr_number), "meta")
# Results in: "pr:myorg:myrepo:123:meta"
```

**Cache key rules:**
- All inputs validated before key construction
- No user input directly in cache keys without validation
- Pattern matching (`invalidate_pattern`) only uses validated inputs
- Colon (`:`) used as delimiter, validated out of inputs

### Error Message Redaction

Error messages MUST NOT leak sensitive data:

```python
class RedactedError(Exception):
    """Exception with sensitive data redacted."""

    def __init__(self, message: str, original: Exception | None = None):
        self.original = original
        super().__init__(message)

def redact_error(error: Exception) -> RedactedError:
    """Redact sensitive information from error messages."""
    message = str(error)

    # Redact potential tokens (ghp_, gho_, github_pat_)
    message = re.sub(r'(ghp_|gho_|github_pat_)[a-zA-Z0-9_]+', '<REDACTED_TOKEN>', message)

    # Redact URLs with credentials
    message = re.sub(r'://[^:]+:[^@]+@', '://<REDACTED>@', message)

    # Redact Authorization headers
    message = re.sub(r'(Authorization["\']?\s*:\s*["\']?)(Bearer\s+)?[a-zA-Z0-9_-]+',
                     r'\1<REDACTED>', message, flags=re.IGNORECASE)

    return RedactedError(message, original=error)
```

**Error handling in CLI:**
```python
try:
    result = analyzer.analyze(owner, repo_name, pr_number)
except Exception as e:
    # Always redact before displaying
    redacted = redact_error(e)
    if verbose:
        click.echo(f"Error: {redacted}", err=True)
    else:
        click.echo("Error: Failed to analyze PR. Use --verbose for details.", err=True)
    sys.exit(4)
```

### Redis Security

When using Redis cache:

```python
def create_redis_cache(redis_url: str) -> RedisCacheAdapter:
    """Create Redis cache with security requirements."""
    parsed = urlparse(redis_url)

    # Warn if not using TLS
    if parsed.scheme == 'redis' and parsed.password:
        import warnings
        warnings.warn(
            "Redis URL contains password but does not use TLS (rediss://). "
            "Consider using TLS for production.",
            SecurityWarning
        )

    # Recommend TLS for production
    # rediss:// scheme enables TLS
    return RedisCacheAdapter(redis_url)
```

**Redis security rules:**
- Recommend `rediss://` (TLS) over `redis://` when credentials present
- Redis URL with password should use TLS in production
- Connection timeouts configured to prevent hanging
- No sensitive data in Redis key names

## Architecture

### Design Principles

- **Library-first**: Core logic is a Python library; CLI is a thin wrapper
- **Ports & Adapters (Hexagonal)**: Core has no external dependencies
- **Dependency Injection**: All dependencies injected via constructors
- **Strategy Pattern**: Pluggable parsers for each reviewer type
- **Repository Pattern**: Cache adapters abstract storage
- **100% Test Coverage**: Branch coverage enforced, no exceptions

### Directory Structure

```
src/goodtogo/
├── core/
│   ├── __init__.py
│   ├── analyzer.py          # PRAnalyzer - main orchestrator
│   ├── models.py            # Pydantic models (PRStatus, Comment, Thread)
│   └── interfaces.py        # Abstract base classes (ports)
├── adapters/
│   ├── __init__.py
│   ├── github.py            # GitHubAdapter (implements GitHubPort)
│   ├── cache_sqlite.py      # SqliteCacheAdapter
│   ├── cache_redis.py       # RedisCacheAdapter
│   └── cache_memory.py      # InMemoryCacheAdapter (for testing)
├── parsers/
│   ├── __init__.py
│   ├── base.py              # BaseReviewerParser (abstract)
│   ├── coderabbit.py        # CodeRabbitParser
│   ├── greptile.py          # GreptileParser
│   ├── claude.py            # ClaudeCodeParser
│   ├── cursor.py            # CursorBugbotParser
│   └── generic.py           # GenericParser (fallback)
├── container.py             # DI container
├── cli.py                   # Thin CLI wrapper
└── __init__.py              # Public API exports
```

### Dependency Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                        (cli.py)                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      Core Layer                              │
│              (analyzer.py, models.py)                        │
│                                                              │
│  PRAnalyzer orchestrates:                                    │
│  - GitHubPort (interface)                                    │
│  - CachePort (interface)                                     │
│  - ReviewerParser (interface)                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Adapter Layer                             │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ GitHubAdapter│  │CacheAdapters│  │  ReviewerParsers    │  │
│  │ (REST/GraphQL)│  │SQLite/Redis │  │ CodeRabbit/Greptile │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Models

### Enums

```python
from enum import Enum

class PRStatus(str, Enum):
    """Final PR status - maps to exit codes."""
    READY = "READY"                      # Exit 0: All clear, ready to merge
    ACTION_REQUIRED = "ACTION_REQUIRED"  # Exit 1: Actionable comments exist
    UNRESOLVED_THREADS = "UNRESOLVED"    # Exit 2: Unresolved threads exist
    CI_FAILING = "CI_FAILING"            # Exit 3: CI/CD checks failing
    ERROR = "ERROR"                      # Exit 4: Error fetching data

class CommentClassification(str, Enum):
    """Comment classification result."""
    ACTIONABLE = "ACTIONABLE"          # Must be addressed
    NON_ACTIONABLE = "NON_ACTIONABLE"  # Can be ignored
    AMBIGUOUS = "AMBIGUOUS"            # Needs agent investigation

class Priority(str, Enum):
    """Comment priority level."""
    CRITICAL = "CRITICAL"  # 🔴 Must fix immediately
    MAJOR = "MAJOR"        # 🟠 Must fix before merge
    MINOR = "MINOR"        # 🟡 Should fix
    TRIVIAL = "TRIVIAL"    # 🔵 Nice to fix
    UNKNOWN = "UNKNOWN"    # Could not determine

class ReviewerType(str, Enum):
    """Automated reviewer identification."""
    CODERABBIT = "coderabbit"
    GREPTILE = "greptile"
    CLAUDE = "claude"
    CURSOR = "cursor"
    HUMAN = "human"
    UNKNOWN = "unknown"
```

### Core Models

```python
from pydantic import BaseModel

class Comment(BaseModel):
    """Individual comment with classification."""
    id: str
    author: str
    reviewer_type: ReviewerType
    body: str
    classification: CommentClassification
    priority: Priority
    requires_investigation: bool  # True if AMBIGUOUS
    thread_id: str | None
    is_resolved: bool
    is_outdated: bool
    file_path: str | None
    line_number: int | None
    created_at: str
    addressed_in_commit: str | None  # SHA if addressed

class CICheck(BaseModel):
    """Individual CI check status."""
    name: str
    status: str  # "success", "failure", "pending"
    conclusion: str | None
    url: str | None

class CIStatus(BaseModel):
    """Aggregate CI status."""
    state: str  # "success", "failure", "pending"
    total_checks: int
    passed: int
    failed: int
    pending: int
    checks: list[CICheck]

class ThreadSummary(BaseModel):
    """Thread resolution summary."""
    total: int
    resolved: int
    unresolved: int
    outdated: int

class CacheStats(BaseModel):
    """Cache performance metrics."""
    hits: int
    misses: int
    hit_rate: float

class PRAnalysisResult(BaseModel):
    """Complete PR analysis result - main output."""
    status: PRStatus
    pr_number: int
    repo_owner: str
    repo_name: str
    latest_commit_sha: str
    latest_commit_timestamp: str
    ci_status: CIStatus
    threads: ThreadSummary
    comments: list[Comment]
    actionable_comments: list[Comment]  # Filtered convenience list
    ambiguous_comments: list[Comment]   # Requires investigation
    action_items: list[str]             # Human-readable summary
    needs_action: bool
    cache_stats: CacheStats | None
```

## Interfaces (Ports)

```python
from abc import ABC, abstractmethod

class GitHubPort(ABC):
    """Abstract interface for GitHub API access."""

    @abstractmethod
    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch PR metadata."""
        pass

    @abstractmethod
    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch all PR comments (inline + review + issue)."""
        pass

    @abstractmethod
    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch all PR reviews."""
        pass

    @abstractmethod
    def get_pr_threads(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch all review threads with resolution status."""
        pass

    @abstractmethod
    def get_ci_status(self, owner: str, repo: str, ref: str) -> dict:
        """Fetch CI/CD check status for a commit."""
        pass


class CachePort(ABC):
    """Abstract interface for caching."""

    @abstractmethod
    def get(self, key: str) -> str | None:
        """Get cached value."""
        pass

    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set cached value with TTL."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete cached value."""
        pass

    @abstractmethod
    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern."""
        pass

    @abstractmethod
    def cleanup_expired(self) -> None:
        """Remove expired entries."""
        pass

    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache hit/miss statistics."""
        pass


class ReviewerParser(ABC):
    """Abstract interface for reviewer-specific parsing."""

    @property
    @abstractmethod
    def reviewer_type(self) -> ReviewerType:
        """Return the reviewer type this parser handles."""
        pass

    @abstractmethod
    def can_parse(self, author: str, body: str) -> bool:
        """Check if this parser can handle the comment."""
        pass

    @abstractmethod
    def parse(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """
        Parse comment and return classification.

        Returns:
            (classification, priority, requires_investigation)
        """
        pass
```

## Comment Classification Rules

### CodeRabbit Parser

| Pattern | Classification | Priority |
|---------|---------------|----------|
| `_⚠️ Potential issue_ \| _🔴 Critical_` | ACTIONABLE | CRITICAL |
| `_⚠️ Potential issue_ \| _🟠 Major_` | ACTIONABLE | MAJOR |
| `_⚠️ Potential issue_ \| _🟡 Minor_` | ACTIONABLE | MINOR |
| `_🔵 Trivial_` | NON_ACTIONABLE | TRIVIAL |
| `_🧹 Nitpick_` | NON_ACTIONABLE | TRIVIAL |
| `<!-- fingerprinting:` | NON_ACTIONABLE | - |
| `✅ Addressed in commits` | NON_ACTIONABLE | - |
| `Outside diff range` (in review body) | ACTIONABLE | MINOR |
| Other | AMBIGUOUS | UNKNOWN |

### Greptile Parser

| Pattern | Classification | Priority |
|---------|---------------|----------|
| `Actionable comments posted: 0` | NON_ACTIONABLE | - |
| `Actionable comments posted: N` (N > 0) | ACTIONABLE | MINOR |
| Review summary only | NON_ACTIONABLE | - |

### Cursor/Bugbot Parser

| Pattern | Classification | Priority |
|---------|---------------|----------|
| `Critical Severity` | ACTIONABLE | CRITICAL |
| `High Severity` | ACTIONABLE | MAJOR |
| `Medium Severity` | ACTIONABLE | MINOR |
| `Low Severity` | NON_ACTIONABLE | TRIVIAL |
| Suggestion without severity | AMBIGUOUS | UNKNOWN |

### Claude Code Parser

| Pattern | Classification | Priority |
|---------|---------------|----------|
| Contains "must", "should fix", "error", "bug" | ACTIONABLE | MINOR |
| Contains "consider", "suggestion", "might" | AMBIGUOUS | UNKNOWN |
| LGTM / approval | NON_ACTIONABLE | - |

### Generic Parser (Fallback)

| Pattern | Classification | Priority |
|---------|---------------|----------|
| Thread is resolved | NON_ACTIONABLE | - |
| Thread is outdated | NON_ACTIONABLE | - |
| Contains reply from PR author | NON_ACTIONABLE | - |
| All other | AMBIGUOUS | UNKNOWN |

**Critical rule**: If AMBIGUOUS, set `requires_investigation=True`. Never silently skip.

## Dependency Injection

```python
# goodtogo/container.py
from dataclasses import dataclass

@dataclass
class Container:
    """DI container - all dependencies injected, no global state."""
    github: GitHubPort
    cache: CachePort
    parsers: dict[ReviewerType, ReviewerParser]

    @classmethod
    def create_default(
        cls,
        github_token: str,
        cache_type: str = "sqlite",
        cache_path: str = ".goodtogo/cache.db",
        redis_url: str | None = None,
    ) -> "Container":
        """Factory for standard configuration."""
        cache = _create_cache(cache_type, cache_path, redis_url)
        return cls(
            github=GitHubAdapter(token=github_token),
            cache=cache,
            parsers=_create_default_parsers(),
        )

    @classmethod
    def create_for_testing(
        cls,
        github: GitHubPort | None = None,
        cache: CachePort | None = None,
    ) -> "Container":
        """Factory for tests - all mocks by default."""
        return cls(
            github=github or MockGitHubAdapter(),
            cache=cache or InMemoryCacheAdapter(),
            parsers=_create_default_parsers(),
        )


def _create_cache(cache_type: str, path: str, redis_url: str | None) -> CachePort:
    """Create cache adapter based on type."""
    if cache_type == "sqlite":
        return SqliteCacheAdapter(path)
    elif cache_type == "redis":
        if not redis_url:
            raise ValueError("redis_url required for redis cache")
        return RedisCacheAdapter(redis_url)
    elif cache_type == "none":
        return NoCacheAdapter()
    else:
        raise ValueError(f"Unknown cache type: {cache_type}")


def _create_default_parsers() -> dict[ReviewerType, ReviewerParser]:
    """Create default parser registry."""
    return {
        ReviewerType.CODERABBIT: CodeRabbitParser(),
        ReviewerType.GREPTILE: GreptileParser(),
        ReviewerType.CLAUDE: ClaudeCodeParser(),
        ReviewerType.CURSOR: CursorBugbotParser(),
        ReviewerType.HUMAN: GenericParser(),
        ReviewerType.UNKNOWN: GenericParser(),
    }
```

## Public API

```python
# goodtogo/__init__.py
"""
Good To Go - Deterministic PR readiness detection for AI agents.

Usage:
    from goodtogo import PRAnalyzer, Container

    container = Container.create_default(github_token="ghp_...")
    analyzer = PRAnalyzer(container)
    result = analyzer.analyze(owner="foo", repo="bar", pr_number=123)

    if result.status == PRStatus.READY:
        print("PR is ready to merge!")
    else:
        for item in result.action_items:
            print(f"- {item}")
"""

from goodtogo.core.analyzer import PRAnalyzer
from goodtogo.core.models import (
    PRAnalysisResult,
    PRStatus,
    Comment,
    CommentClassification,
    Priority,
    ReviewerType,
    CIStatus,
    ThreadSummary,
)
from goodtogo.container import Container

__version__ = "0.1.0"

__all__ = [
    "PRAnalyzer",
    "Container",
    "PRAnalysisResult",
    "PRStatus",
    "Comment",
    "CommentClassification",
    "Priority",
    "ReviewerType",
    "CIStatus",
    "ThreadSummary",
]
```

## CLI Interface

```python
# goodtogo/cli.py
"""Thin CLI wrapper around PRAnalyzer."""

import json
import os
import sys

import click

from goodtogo import PRAnalyzer, Container, PRStatus


EXIT_CODES = {
    PRStatus.READY: 0,
    PRStatus.ACTION_REQUIRED: 1,
    PRStatus.UNRESOLVED_THREADS: 2,
    PRStatus.CI_FAILING: 3,
    PRStatus.ERROR: 4,
}


@click.command()
@click.argument("pr_number", type=int)
@click.option("--repo", "-r", required=True, help="Repository in owner/repo format")
@click.option(
    "--cache",
    type=click.Choice(["sqlite", "redis", "none"]),
    default="sqlite",
    help="Cache backend (default: sqlite)",
)
@click.option(
    "--cache-path",
    default=".goodtogo/cache.db",
    help="SQLite cache path",
)
@click.option(
    "--redis-url",
    envvar="REDIS_URL",
    help="Redis URL (required if --cache=redis)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "text"]),
    default="json",
    help="Output format (default: json)",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.version_option()
def main(
    pr_number: int,
    repo: str,
    cache: str,
    cache_path: str,
    redis_url: str | None,
    output_format: str,
    verbose: bool,
) -> None:
    """Check if a PR is ready to merge.

    Exit codes:
      0 - Ready to merge
      1 - Actionable comments need addressing
      2 - Unresolved threads exist
      3 - CI/CD checks failing
      4 - Error fetching data
    """
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        click.echo("Error: GITHUB_TOKEN environment variable required", err=True)
        sys.exit(4)

    try:
        owner, repo_name = repo.split("/")
    except ValueError:
        click.echo("Error: --repo must be in owner/repo format", err=True)
        sys.exit(4)

    try:
        container = Container.create_default(
            github_token=github_token,
            cache_type=cache,
            cache_path=cache_path,
            redis_url=redis_url,
        )
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze(owner, repo_name, pr_number)
    except Exception as e:
        if verbose:
            click.echo(f"Error: {e}", err=True)
        sys.exit(4)

    if output_format == "json":
        click.echo(result.model_dump_json(indent=2))
    else:
        _print_text_output(result, verbose)

    sys.exit(EXIT_CODES[result.status])


def _print_text_output(result, verbose: bool) -> None:
    """Print human-readable output."""
    status_icons = {
        PRStatus.READY: "✅",
        PRStatus.ACTION_REQUIRED: "⚠️",
        PRStatus.UNRESOLVED_THREADS: "💬",
        PRStatus.CI_FAILING: "❌",
        PRStatus.ERROR: "🚨",
    }

    icon = status_icons.get(result.status, "❓")
    click.echo(f"{icon} PR #{result.pr_number}: {result.status.value}")
    click.echo(f"   CI: {result.ci_status.state} ({result.ci_status.passed}/{result.ci_status.total_checks} passed)")
    click.echo(f"   Threads: {result.threads.resolved}/{result.threads.total} resolved")

    if result.action_items:
        click.echo("\nAction required:")
        for item in result.action_items:
            click.echo(f"   - {item}")

    if verbose and result.ambiguous_comments:
        click.echo("\nAmbiguous (needs investigation):")
        for comment in result.ambiguous_comments:
            click.echo(f"   - [{comment.author}] {comment.body[:80]}...")


if __name__ == "__main__":
    main()
```

## Caching Strategy

### Cache Keys

```
pr:{owner}:{repo}:{pr}:meta                    → TTL: 5m (PR metadata)
pr:{owner}:{repo}:{pr}:commit:latest           → TTL: 5m (latest SHA)
pr:{owner}:{repo}:{pr}:comment:{id}            → TTL: 24h (immutable)
pr:{owner}:{repo}:{pr}:thread:{id}:resolved    → TTL: 24h (after resolved)
pr:{owner}:{repo}:{pr}:ci:status               → TTL: 5m (while pending), 24h (after complete)
pr:{owner}:{repo}:{pr}:analysis:timestamp      → TTL: 1m (rate limit protection)
```

### Cache Invalidation

```python
# Invalidate on new commit
if latest_commit_sha != cached_commit_sha:
    cache.invalidate_pattern(f"pr:{owner}:{repo}:{pr}:*")

# Cleanup expired entries periodically
cache.cleanup_expired()
```

### SQLite Schema

```sql
CREATE TABLE pr_cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX idx_expires_at ON pr_cache(expires_at);

CREATE TABLE cache_stats (
    key_prefix TEXT PRIMARY KEY,
    hits INTEGER DEFAULT 0,
    misses INTEGER DEFAULT 0
);
```

## Testing Strategy

### Test Structure

```
tests/
├── unit/
│   ├── core/
│   │   ├── test_analyzer.py         # PRAnalyzer with mocked adapters
│   │   └── test_models.py           # Pydantic model validation
│   ├── parsers/
│   │   ├── test_coderabbit.py       # CodeRabbit patterns
│   │   ├── test_greptile.py         # Greptile patterns
│   │   ├── test_claude.py           # Claude Code patterns
│   │   ├── test_cursor.py           # Cursor/Bugbot patterns
│   │   └── test_generic.py          # Fallback/ambiguous cases
│   └── adapters/
│       ├── test_cache_sqlite.py     # SQLite operations
│       ├── test_cache_redis.py      # Redis operations (mocked)
│       ├── test_cache_memory.py     # In-memory cache
│       └── test_github.py           # GitHub API (mocked)
├── integration/
│   ├── test_cli.py                  # End-to-end CLI tests
│   └── test_full_analysis.py        # Complete flow tests
├── fixtures/
│   ├── comments/
│   │   ├── coderabbit.json          # Generic CodeRabbit examples
│   │   ├── greptile.json            # Generic Greptile examples
│   │   ├── claude.json              # Generic Claude examples
│   │   └── cursor.json              # Generic Cursor examples
│   ├── prs/
│   │   ├── ready_to_merge.json      # All clear scenario
│   │   ├── action_required.json     # Actionable comments
│   │   ├── unresolved_threads.json  # Unresolved threads
│   │   └── ci_failing.json          # CI failure scenario
│   └── conftest.py                  # Shared fixtures
└── conftest.py                      # Root fixtures, DI setup
```

### Coverage Requirements

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=goodtogo --cov-report=term-missing --cov-fail-under=100"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["src/goodtogo"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@abstractmethod",
]
fail_under = 100
```

### Test Fixtures (Genericized)

```json
// tests/fixtures/comments/coderabbit.json
{
  "actionable_critical": {
    "author": "coderabbitai[bot]",
    "body": "_⚠️ Potential issue_ | _🔴 Critical_\n\n**SQL injection vulnerability detected.**\n\nUser input is passed directly to query without sanitization.",
    "expected": {
      "classification": "ACTIONABLE",
      "priority": "CRITICAL",
      "requires_investigation": false
    }
  },
  "actionable_minor": {
    "author": "coderabbitai[bot]",
    "body": "_⚠️ Potential issue_ | _🟡 Minor_\n\n**Add language identifier to code block.**",
    "expected": {
      "classification": "ACTIONABLE",
      "priority": "MINOR",
      "requires_investigation": false
    }
  },
  "non_actionable_nitpick": {
    "author": "coderabbitai[bot]",
    "body": "_🧹 Nitpick_\n\nConsider using a more descriptive variable name.",
    "expected": {
      "classification": "NON_ACTIONABLE",
      "priority": "TRIVIAL",
      "requires_investigation": false
    }
  },
  "non_actionable_resolved": {
    "author": "coderabbitai[bot]",
    "body": "✅ Addressed in commits abc1234 to def5678",
    "expected": {
      "classification": "NON_ACTIONABLE",
      "priority": "UNKNOWN",
      "requires_investigation": false
    }
  },
  "non_actionable_fingerprint": {
    "author": "coderabbitai[bot]",
    "body": "<!-- fingerprinting:phantom:triton:puma -->",
    "expected": {
      "classification": "NON_ACTIONABLE",
      "priority": "UNKNOWN",
      "requires_investigation": false
    }
  }
}
```

### Security Test Specifications

All security requirements MUST have explicit test coverage. Tests are organized by security domain.

#### Input Validation Tests (`tests/unit/security/test_input_validation.py`)

```python
"""
Tests for input validation boundaries.
Coverage target: 100% branch coverage on all validation functions.
"""

import pytest
from goodtogo.core.validation import (
    validate_github_identifier,
    validate_pr_number,
)


class TestGitHubIdentifierValidation:
    """Boundary tests for validate_github_identifier()."""

    # --- Empty/Null boundaries ---
    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_github_identifier("", "owner")

    def test_whitespace_only_raises_value_error(self):
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("   ", "owner")

    # --- Length boundaries (GitHub max: 39 characters) ---
    def test_single_character_valid(self):
        assert validate_github_identifier("a", "owner") == "a"

    def test_39_characters_valid(self):
        valid_39 = "a" * 39
        assert validate_github_identifier(valid_39, "owner") == valid_39

    def test_40_characters_raises_value_error(self):
        invalid_40 = "a" * 40
        with pytest.raises(ValueError, match="exceeds maximum length"):
            validate_github_identifier(invalid_40, "owner")

    # --- Character boundaries ---
    def test_alphanumeric_only_valid(self):
        assert validate_github_identifier("abc123", "owner") == "abc123"

    def test_with_hyphen_valid(self):
        assert validate_github_identifier("my-org", "owner") == "my-org"

    def test_with_underscore_valid(self):
        assert validate_github_identifier("my_org", "owner") == "my_org"

    def test_with_dot_valid(self):
        assert validate_github_identifier("my.org", "owner") == "my.org"

    def test_starts_with_hyphen_raises(self):
        with pytest.raises(ValueError, match="starting and ending with alphanumeric"):
            validate_github_identifier("-invalid", "owner")

    def test_ends_with_hyphen_raises(self):
        with pytest.raises(ValueError, match="starting and ending with alphanumeric"):
            validate_github_identifier("invalid-", "owner")

    def test_starts_with_dot_raises(self):
        with pytest.raises(ValueError, match="starting and ending with alphanumeric"):
            validate_github_identifier(".invalid", "owner")

    # --- Injection attempt boundaries ---
    def test_slash_raises_value_error(self):
        """Path traversal attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("../etc/passwd", "owner")

    def test_semicolon_raises_value_error(self):
        """Command injection attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("valid;rm -rf", "owner")

    def test_backtick_raises_value_error(self):
        """Command substitution attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("valid`id`", "owner")

    def test_null_byte_raises_value_error(self):
        """Null byte injection attempt."""
        with pytest.raises(ValueError, match="contains invalid characters"):
            validate_github_identifier("valid\x00evil", "owner")


class TestPRNumberValidation:
    """Boundary tests for validate_pr_number()."""

    # --- Zero boundary ---
    def test_zero_raises_value_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_pr_number(0)

    def test_negative_raises_value_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_pr_number(-1)

    # --- Positive boundary ---
    def test_one_valid(self):
        assert validate_pr_number(1) == 1

    # --- Upper boundary (int32 max) ---
    def test_int32_max_valid(self):
        assert validate_pr_number(2147483647) == 2147483647

    def test_int32_max_plus_one_raises(self):
        with pytest.raises(ValueError, match="exceeds maximum value"):
            validate_pr_number(2147483648)
```

#### Token Security Tests (`tests/unit/security/test_token_security.py`)

```python
"""
Tests for token redaction and protection.
Coverage target: 100% branch coverage on all token handling.
"""

import pytest
from goodtogo.adapters.github import GitHubAdapter
from goodtogo.core.errors import redact_error


class TestGitHubAdapterTokenProtection:
    """Verify tokens never leak through repr/str."""

    def test_repr_redacts_token(self):
        adapter = GitHubAdapter(token="ghp_secret123456789")
        repr_output = repr(adapter)
        assert "ghp_secret123456789" not in repr_output
        assert "<redacted>" in repr_output.lower()

    def test_str_redacts_token(self):
        adapter = GitHubAdapter(token="ghp_secret123456789")
        str_output = str(adapter)
        assert "ghp_secret123456789" not in str_output
        assert "<redacted>" in str_output.lower()

    def test_token_not_in_dict(self):
        """Token should not appear if adapter is serialized."""
        adapter = GitHubAdapter(token="ghp_secret123456789")
        # Attempting to get __dict__ or vars() should not expose token
        if hasattr(adapter, "__dict__"):
            dict_str = str(adapter.__dict__)
            # Token should be in private attribute only
            assert "ghp_secret123456789" not in dict_str.replace("_token", "")


class TestErrorRedaction:
    """Verify error messages redact sensitive patterns."""

    # --- GitHub Personal Access Token patterns ---
    @pytest.mark.parametrize("token_prefix", [
        "ghp_",   # GitHub Personal Access Token
        "gho_",   # GitHub OAuth Token
        "github_pat_",  # GitHub PAT (newer format)
    ])
    def test_github_token_patterns_redacted(self, token_prefix):
        """All GitHub token prefixes must be redacted."""
        token = f"{token_prefix}abcdefghijklmnop1234567890"
        error = Exception(f"Authentication failed: {token}")
        redacted = redact_error(error)
        assert token not in str(redacted)
        assert "<REDACTED_TOKEN>" in str(redacted)

    def test_ghp_token_in_url_redacted(self):
        """Token in URL query params must be redacted."""
        error = Exception("Failed: https://api.github.com?token=ghp_secret123")
        redacted = redact_error(error)
        assert "ghp_secret123" not in str(redacted)

    def test_gho_token_redacted(self):
        error = Exception("OAuth token gho_abc123xyz789 is invalid")
        redacted = redact_error(error)
        assert "gho_abc123xyz789" not in str(redacted)

    def test_github_pat_token_redacted(self):
        error = Exception("PAT github_pat_22A_verylongtoken123 expired")
        redacted = redact_error(error)
        assert "github_pat_22A_verylongtoken123" not in str(redacted)

    # --- URL credential patterns ---
    def test_url_basic_auth_redacted(self):
        """user:pass@host pattern must be redacted."""
        error = Exception("Failed to connect: https://user:ghp_secret@github.com/repo")
        redacted = redact_error(error)
        assert "ghp_secret" not in str(redacted)
        assert "<REDACTED>" in str(redacted)

    # --- Authorization header patterns ---
    def test_authorization_bearer_redacted(self):
        """Authorization: Bearer <token> must be redacted."""
        error = Exception('Header: {"Authorization": "Bearer ghp_secret123"}')
        redacted = redact_error(error)
        assert "ghp_secret123" not in str(redacted)

    def test_authorization_token_redacted(self):
        """Authorization: token <token> must be redacted."""
        error = Exception("Authorization: token ghp_verysecret")
        redacted = redact_error(error)
        assert "ghp_verysecret" not in str(redacted)

    # --- Verify original exception preserved ---
    def test_original_exception_preserved(self):
        original = ValueError("ghp_secret123 is invalid")
        redacted = redact_error(original)
        assert redacted.original is original
        assert isinstance(redacted.original, ValueError)
```

#### File Permission Tests (`tests/unit/security/test_file_permissions.py`)

```python
"""
Tests for SQLite cache file permissions.
Coverage target: 100% branch coverage on permission handling.
"""

import os
import stat
import tempfile
import pytest
from goodtogo.adapters.cache_sqlite import SqliteCacheAdapter


class TestSQLiteCachePermissions:
    """Verify cache files have secure permissions."""

    def test_new_cache_file_has_0600_permissions(self):
        """New cache file must be created with 0600 (owner rw only)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            cache = SqliteCacheAdapter(cache_path)
            cache.set("test", "value", ttl_seconds=60)

            # Check permissions
            mode = os.stat(cache_path).st_mode
            # Extract permission bits
            perms = stat.S_IMODE(mode)
            assert perms == 0o600, f"Expected 0600, got {oct(perms)}"

    def test_cache_directory_has_0700_permissions(self):
        """Cache directory must be created with 0700."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "subdir", "cache")
            cache_path = os.path.join(cache_dir, "cache.db")
            cache = SqliteCacheAdapter(cache_path)
            cache.set("test", "value", ttl_seconds=60)

            # Check directory permissions
            mode = os.stat(cache_dir).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o700, f"Expected 0700, got {oct(perms)}"

    def test_existing_permissive_file_gets_restricted(self):
        """If file exists with loose perms, must be tightened."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            # Create file with permissive permissions
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o666)

            # Open cache - should fix permissions
            cache = SqliteCacheAdapter(cache_path)

            # Verify permissions were fixed
            mode = os.stat(cache_path).st_mode
            perms = stat.S_IMODE(mode)
            assert perms == 0o600, f"Expected 0600, got {oct(perms)}"

    def test_permission_warning_logged_for_world_readable(self):
        """Log warning if file was world-readable before fix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "cache.db")
            with open(cache_path, "w") as f:
                f.write("")
            os.chmod(cache_path, 0o644)  # World readable

            with pytest.warns(UserWarning, match="permissive"):
                cache = SqliteCacheAdapter(cache_path)
```

#### Cache Key Sanitization Tests (`tests/unit/security/test_cache_key_sanitization.py`)

```python
"""
Tests for cache key sanitization.
Coverage target: 100% branch coverage on cache key construction.
"""

import pytest
from goodtogo.core.cache import build_cache_key


class TestCacheKeySanitization:
    """Verify cache keys are safely constructed."""

    # --- Valid key construction ---
    def test_valid_parts_create_key(self):
        key = build_cache_key("pr", "myorg", "myrepo", "123", "meta")
        assert key == "pr:myorg:myrepo:123:meta"

    def test_numeric_parts_converted_to_string(self):
        key = build_cache_key("pr", "org", "repo", 123, "ci")
        assert key == "pr:org:repo:123:ci"

    # --- Colon rejection (delimiter collision) ---
    def test_colon_in_owner_raises(self):
        """Colons would corrupt key structure."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "my:org", "repo", "123")

    def test_colon_in_repo_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "my:repo", "123")

    def test_colon_in_suffix_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo", "123", "meta:data")

    # --- Asterisk rejection (glob pattern safety) ---
    def test_asterisk_in_owner_raises(self):
        """Asterisks could cause unintended pattern matches."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "my*org", "repo", "123")

    def test_asterisk_in_repo_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "*repo", "123")

    def test_asterisk_alone_raises(self):
        """Wildcard injection attempt."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo", "*")

    # --- Question mark rejection (glob pattern safety) ---
    def test_question_mark_in_owner_raises(self):
        """Question marks are glob single-char wildcards."""
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "my?org", "repo", "123")

    def test_question_mark_in_repo_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo?name", "123")

    # --- Combined injection attempts ---
    def test_combined_special_chars_raises(self):
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org:*?", "repo", "123")

    # --- Empty parts ---
    def test_empty_part_in_middle_raises(self):
        """Empty parts would create malformed keys."""
        with pytest.raises(ValueError, match="empty"):
            build_cache_key("pr", "org", "", "123")

    # --- Pre-validated inputs (defense in depth) ---
    def test_validates_even_if_inputs_already_validated(self):
        """
        Even if caller validated inputs, build_cache_key should
        still reject special characters (defense in depth).
        """
        # Simulating a bug where validation was bypassed
        with pytest.raises(ValueError, match="Invalid character"):
            build_cache_key("pr", "org", "repo:injection", "123")
```

#### Error Path Redaction Tests (`tests/unit/security/test_error_paths.py`)

```python
"""
Tests verifying token redaction in all error paths.
Coverage target: All error paths must redact sensitive data.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from goodtogo.cli import main
from goodtogo.core.analyzer import PRAnalyzer


class TestCLIErrorRedaction:
    """Verify CLI error output redacts tokens."""

    def test_github_api_error_redacts_token(self):
        """Token in API error must not appear in output."""
        runner = CliRunner()
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_supersecret123"}):
            with patch("goodtogo.container.Container.create_default") as mock:
                mock.side_effect = Exception(
                    "API error: token ghp_supersecret123 is invalid"
                )
                result = runner.invoke(main, ["123", "--repo", "org/repo", "-v"])
                assert "ghp_supersecret123" not in result.output
                assert result.exit_code == 4

    def test_connection_error_redacts_url_credentials(self):
        """Credentials in connection URLs must be redacted."""
        runner = CliRunner()
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test"}):
            with patch("goodtogo.container.Container.create_default") as mock:
                mock.side_effect = Exception(
                    "Connection failed: https://ghp_test:x-oauth@api.github.com"
                )
                result = runner.invoke(main, ["123", "--repo", "org/repo", "-v"])
                assert "ghp_test" not in result.output

    def test_non_verbose_hides_details(self):
        """Without --verbose, error details should be hidden."""
        runner = CliRunner()
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test"}):
            with patch("goodtogo.container.Container.create_default") as mock:
                mock.side_effect = Exception("Detailed error with ghp_secret")
                result = runner.invoke(main, ["123", "--repo", "org/repo"])
                # Should show generic message, not details
                assert "Use --verbose for details" in result.output
                assert "ghp_secret" not in result.output


class TestAnalyzerErrorRedaction:
    """Verify analyzer exceptions are redacted."""

    def test_github_port_error_redacted(self):
        """Errors from GitHub port must be redacted before propagating."""
        from goodtogo.container import Container

        container = Container.create_for_testing()
        container.github.get_pr = MagicMock(
            side_effect=Exception("Auth failed: ghp_leaked123")
        )
        analyzer = PRAnalyzer(container)

        with pytest.raises(Exception) as exc_info:
            analyzer.analyze("org", "repo", 123)

        # The raised exception should have redacted message
        assert "ghp_leaked123" not in str(exc_info.value)

    def test_cache_error_redacted(self):
        """Errors from cache layer must be redacted."""
        from goodtogo.container import Container

        container = Container.create_for_testing()
        container.cache.get = MagicMock(
            side_effect=Exception("Redis auth: password=ghp_cachetoken")
        )
        analyzer = PRAnalyzer(container)

        with pytest.raises(Exception) as exc_info:
            analyzer.analyze("org", "repo", 123)

        assert "ghp_cachetoken" not in str(exc_info.value)
```

## Output Format

### JSON Output (Default)

```json
{
  "status": "ACTION_REQUIRED",
  "pr_number": 123,
  "repo_owner": "example",
  "repo_name": "project",
  "latest_commit_sha": "abc123def456",
  "latest_commit_timestamp": "2026-01-15T10:30:00Z",
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
    "total": 8,
    "resolved": 5,
    "unresolved": 3,
    "outdated": 0
  },
  "comments": [...],
  "actionable_comments": [
    {
      "id": "comment_123",
      "author": "coderabbitai[bot]",
      "reviewer_type": "coderabbit",
      "body": "_⚠️ Potential issue_ | _🟡 Minor_\n\n**Add error handling.**",
      "classification": "ACTIONABLE",
      "priority": "MINOR",
      "requires_investigation": false,
      "thread_id": "thread_456",
      "is_resolved": false,
      "is_outdated": false,
      "file_path": "src/main.py",
      "line_number": 42,
      "created_at": "2026-01-15T09:00:00Z",
      "addressed_in_commit": null
    }
  ],
  "ambiguous_comments": [
    {
      "id": "comment_789",
      "author": "contributor",
      "reviewer_type": "human",
      "body": "This might need refactoring",
      "classification": "AMBIGUOUS",
      "priority": "UNKNOWN",
      "requires_investigation": true,
      ...
    }
  ],
  "action_items": [
    "3 actionable comments need addressing",
    "1 comment requires investigation (ambiguous)"
  ],
  "needs_action": true,
  "cache_stats": {
    "hits": 12,
    "misses": 3,
    "hit_rate": 0.8
  }
}
```

### Exit Codes

| Code | Status | Meaning |
|------|--------|---------|
| 0 | READY | All clear, PR ready to merge |
| 1 | ACTION_REQUIRED | Actionable comments need addressing |
| 2 | UNRESOLVED_THREADS | Unresolved review threads exist |
| 3 | CI_FAILING | CI/CD checks are failing |
| 4 | ERROR | Error fetching data from GitHub |

## Usage Examples

### Library Usage

```python
from goodtogo import PRAnalyzer, Container, PRStatus

# Create container with default configuration
container = Container.create_default(
    github_token="ghp_...",
    cache_type="sqlite",
)

# Create analyzer
analyzer = PRAnalyzer(container)

# Analyze PR
result = analyzer.analyze(owner="myorg", repo="myrepo", pr_number=123)

# Check status
if result.status == PRStatus.READY:
    print("PR is ready to merge!")
elif result.status == PRStatus.ACTION_REQUIRED:
    print(f"Action required: {len(result.actionable_comments)} comments")
    for comment in result.actionable_comments:
        print(f"  - [{comment.priority}] {comment.body[:50]}...")
elif result.status == PRStatus.UNRESOLVED_THREADS:
    print(f"Unresolved threads: {result.threads.unresolved}")
```

### CLI Usage

```bash
# Basic usage
gtm check 123 --repo myorg/myrepo

# With options
gtm check 123 --repo myorg/myrepo --format text --verbose

# Use Redis cache
gtm check 123 --repo myorg/myrepo --cache redis --redis-url redis://localhost:6379

# Skip cache
gtm check 123 --repo myorg/myrepo --cache none

# In scripts
if gtm check 123 --repo myorg/myrepo; then
    echo "Ready to merge"
else
    echo "Action required (exit code: $?)"
fi
```

### CI/CD Integration

```yaml
# .github/workflows/pr-check.yml
- name: Check PR Readiness
  run: |
    pip install goodtogo
    gtm check ${{ github.event.pull_request.number }} \
      --repo ${{ github.repository }} \
      --format json > pr-status.json
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Dependencies

### Required

- `pydantic>=2.0` - Data validation and models
- `click>=8.0` - CLI framework
- `httpx>=0.25` - HTTP client for GitHub API

### Optional

- `better-sqlite3` via `sqlean` - SQLite cache (default)
- `redis>=5.0` - Redis cache (optional)

### Development

- `pytest>=7.0`
- `pytest-cov>=4.0`
- `pytest-asyncio>=0.21`
- `hypothesis>=6.0` - Property-based testing
- `mutmut>=2.4` - Mutation testing
- `black>=23.0`
- `ruff>=0.1`
- `mypy>=1.0`

## Success Metrics

| Metric | Target |
|--------|--------|
| Test coverage | 100% (branch coverage) |
| Response time (cached) | < 2 seconds |
| Response time (uncached) | < 10 seconds |
| Cache hit rate | > 80% for active PRs |
| False positive rate | < 5% (informational marked as actionable) |
| False negative rate | 0% (actionable never skipped) |

## Future Considerations (Out of Scope for v0.1)

- Webhook listener for push notifications
- GitHub App integration (vs PAT)
- Support for GitLab, Bitbucket
- Custom parser plugin system
- Web UI dashboard
- Slack/Discord notifications

---

## Appendix: Reviewer Detection

### Author Patterns

| Reviewer | Author Pattern |
|----------|---------------|
| CodeRabbit | `coderabbitai[bot]` |
| Greptile | `greptile[bot]` |
| Claude Code | `claude-code[bot]`, `anthropic-claude[bot]` |
| Cursor/Bugbot | `cursor[bot]`, `cursor-bot` |
| Human | Any other author |

### Body Pattern Detection (Fallback)

If author detection fails, check body patterns:

- CodeRabbit: Contains `<!-- This is an auto-generated comment: ... by coderabbit.ai -->`
- Greptile: Contains `greptile.com` links or `Greptile` branding
- Cursor: Contains `cursor.com` links or Cursor-specific formatting
