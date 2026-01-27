# Contributing to Good To Go

Thank you for your interest in contributing to Good To Go! This guide covers everything you need to set up a development environment.

## Development vs Usage

**If you just want to USE Good To Go**, see the [README](README.md) - you only need:
```bash
pip install gtg
```

**This guide is for DEVELOPING Good To Go itself** - contributing code, fixing bugs, adding features.

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- A GitHub account

### Clone the Repository

```bash
git clone https://github.com/dsifry/goodtogo.git
cd goodtogo
```

### Install Development Dependencies

```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

This installs:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatter
- `ruff` - Linter
- `mypy` - Type checker

### Verify Installation

```bash
# Run tests
pytest

# Check linting
ruff check .

# Check formatting
black --check .

# Check types
mypy src/
```

## Code Quality Requirements

All contributions must pass these checks:

```bash
# Run all checks
pytest && ruff check . && black --check . && mypy src/
```

### Test Coverage

Good To Go requires **100% branch coverage**. Tests will fail if coverage drops below 100%.

```bash
pytest --cov=goodtogo --cov-report=term-missing
```

### Code Style

- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type hints**: Required for all public functions

```bash
# Auto-format code
black .

# Auto-fix lint issues
ruff check . --fix
```

## Project Architecture

Good To Go uses **hexagonal architecture** (ports and adapters):

```
src/goodtogo/
├── core/                 # Business logic (no external dependencies)
│   ├── models.py        # Pydantic data models
│   ├── interfaces.py    # Abstract interfaces (ports)
│   ├── analyzer.py      # Main PR analysis logic
│   ├── validation.py    # Input validation
│   └── errors.py        # Error handling with redaction
├── adapters/            # External integrations (implements ports)
│   ├── github.py        # GitHub API adapter
│   ├── cache_sqlite.py  # SQLite cache adapter
│   ├── cache_memory.py  # In-memory cache (for testing)
│   ├── agent_state.py   # State persistence for dismissals
│   └── time_provider.py # Time abstraction (for testing)
├── parsers/             # Comment parsers (Template Method pattern)
│   ├── coderabbit.py    # CodeRabbit parser
│   ├── greptile.py      # Greptile parser
│   ├── claude.py        # Claude Code parser
│   ├── cursor.py        # Cursor/Bugbot parser
│   └── generic.py       # Fallback parser
├── container.py         # Dependency injection
├── cli.py               # Click CLI
└── __init__.py          # Public exports
```

### Key Principles

1. **Core has no dependencies** - Business logic is pure Python + Pydantic
2. **Adapters implement interfaces** - Easy to swap implementations
3. **Parsers are pluggable** - Add new reviewers without changing core
4. **Dependency injection** - Container wires everything together
5. **Security by design** - Tokens never logged, errors redacted

## Adding a New Reviewer Parser

To support a new automated reviewer:

1. Create `src/goodtogo/parsers/newreviewer.py`:

```python
from goodtogo.core.interfaces import ReviewerParser
from goodtogo.core.models import CommentClassification, Priority, ReviewerType

class NewReviewerParser(ReviewerParser):
    @property
    def reviewer_type(self) -> ReviewerType:
        return ReviewerType.UNKNOWN  # Or add new enum value in models.py

    def can_parse(self, author: str, body: str) -> bool:
        """Check if this parser can handle the comment."""
        return author == "newreviewer[bot]" or "newreviewer.com" in body

    def _parse_impl(self, comment: dict) -> tuple[CommentClassification, Priority, bool]:
        """Parser-specific classification logic.

        Note: Use _parse_impl, not parse(). The base class parse() method
        handles common logic (resolved/outdated threads) via Template Method,
        then delegates to _parse_impl() for parser-specific classification.

        Returns:
            Tuple of (classification, priority, requires_investigation)
            If classification is AMBIGUOUS, requires_investigation MUST be True
        """
        body = comment.get("body", "")

        # Example classification logic
        if "critical" in body.lower():
            return (CommentClassification.ACTIONABLE, Priority.CRITICAL, False)
        if "lgtm" in body.lower():
            return (CommentClassification.NON_ACTIONABLE, Priority.UNKNOWN, False)

        # Default to ambiguous (requires investigation must be True)
        return (CommentClassification.AMBIGUOUS, Priority.UNKNOWN, True)
```

2. Register in `container.py`:

```python
from goodtogo.parsers.newreviewer import NewReviewerParser

# In create_default():
parsers = [
    CodeRabbitParser(),
    GreptileParser(),
    ClaudeCodeParser(),
    CursorBugbotParser(),
    NewReviewerParser(),  # Add here
    GenericParser(),  # Keep generic last (fallback)
]
```

3. Add tests in `tests/unit/parsers/test_newreviewer.py`

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/parsers/test_coderabbit.py

# With coverage report
pytest --cov=goodtogo --cov-report=html
open htmlcov/index.html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Submitting Changes

### Branch Naming

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test improvements

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Be concise but descriptive
- Reference issues if applicable

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all checks pass:
   ```bash
   pytest && ruff check . && black --check . && mypy src/
   ```
5. Push and create a PR

### PR Checklist

- [ ] Tests pass with 100% coverage
- [ ] Code formatted with Black
- [ ] No Ruff warnings
- [ ] Mypy type checks pass
- [ ] Documentation updated if needed

## Optional: Claude Code Workflow Tools

If you use [Claude Code](https://claude.ai/code), Good To Go includes workflow tools in the `.claude/` directory:

### Install Beads (Task Management)

```bash
npm install -g @coderabbitai/beads
bd init --prefix goodtogo
```

### Available Commands

- `/project:pr-shepherd` - Monitor PR to merge
- `/project:handle-pr-comments` - Address review feedback
- `/project:create-pr` - Create comprehensive PR

These are optional developer tools - they're not required for contributing, but they can help streamline your workflow if you use Claude Code.

## Customizing Agents

Good To Go ships with a set of agent definitions that Claude Code can use during workflows like issue orchestration, code review, and PR shepherding. These live in:

```
.claude/plugins/goodtogo/skills/beads/agents/
```

### Available Agents

| Agent | File | Purpose |
|-------|------|---------|
| CTO | `cto-agent.md` | Strategic technical decisions |
| Architect | `architect-agent.md` | System design and architecture |
| Product Manager | `product-manager-agent.md` | Requirements and prioritization |
| Security Design | `security-design-agent.md` | Security architecture review |
| Security Auditor | `security-auditor-agent.md` | Security vulnerability auditing |
| Code Review | `code-review-agent.md` | Code review feedback |
| Coder | `coder-agent.md` | TDD implementation of features and fixes |
| Researcher | `researcher-agent.md` | Research and information gathering |
| Designer | `designer-agent.md` | UI/UX design guidance |
| Test Automator | `test-automator-agent.md` | Test strategy and automation |
| SRE | `sre-agent.md` | Reliability and operations |
| Metrics | `metrics-agent.md` | Analytics and measurement |
| Knowledge Curator | `knowledge-curator-agent.md` | Documentation and knowledge management |
| Customer Service | `customer-service-agent.md` | Customer-facing support |
| PR Shepherd | `pr-shepherd-agent.md` | Monitor PRs through to merge |
| Issue Orchestrator | `issue-orchestrator.md` | Coordinate multi-agent issue resolution |
| Slack Coordinator | `slack-coordinator-agent.md` | Slack integration and notifications |
| Swarm Coordinator | `swarm-coordinator-agent.md` | Multi-agent task coordination |

### Agent File Format

Each agent is a Markdown file with a consistent structure:

```markdown
# Agent Name

**Type**: `agent-type`
**Role**: One-line description
**Spawned By**: Which agent or workflow triggers this one
**Tools**: What tools/capabilities the agent has

---

## Purpose

What this agent does and why it exists.

---

## Responsibilities

1. **Key Responsibility**: Description
2. ...

---

## Activation

Triggered when:
- Condition that causes this agent to activate
- ...
```

Agents may also include sections for workflow steps, input/output contracts, prompts, and error handling.

### Adding a New Agent

1. Create a new Markdown file in the agents directory:

   ```bash
   touch .claude/plugins/goodtogo/skills/beads/agents/my-agent.md
   ```

2. Follow the standard format above. At minimum, include:
   - **Type** and **Role** in the header
   - **Purpose** section explaining what the agent does
   - **Responsibilities** listing its key duties
   - **Activation** describing when it runs

3. If your agent is spawned by another agent (e.g., the Issue Orchestrator), update that agent's file to reference your new agent in its workflow.

### Modifying an Existing Agent

1. Open the agent file you want to change:

   ```bash
   cat .claude/plugins/goodtogo/skills/beads/agents/coder-agent.md
   ```

2. Edit the sections relevant to your change. Common modifications:
   - **Responsibilities**: Add or remove duties
   - **Activation**: Change when the agent triggers
   - **Workflow steps**: Adjust the agent's process
   - **Prompts/templates**: Refine the instructions the agent follows

3. Keep the existing format and section structure intact so other agents and workflows can still reference it consistently.

### Tips

- Agents are documentation-as-configuration — Claude Code reads them to understand how to behave in different roles.
- Keep agent descriptions concrete and actionable. Vague instructions produce vague results.
- If two agents overlap in responsibility, clarify boundaries in both files.
- Test your changes by running the workflow that triggers the agent (e.g., create a test issue to exercise the Issue Orchestrator and its child agents).

## Agent Workflows and Orchestration

Agents don't work in isolation — they're coordinated through workflows that define which agents run, in what order, and how they hand off work. This section explains the orchestration model and how to customize it.

### Orchestration Hierarchy

The agent system has three levels of coordination:

```
Swarm Coordinator          (manages multiple issues in parallel)
  └─ Issue Orchestrator    (drives a single issue from creation to merge)
       ├─ Researcher       (explores codebase, gathers context)
       ├─ Architect        (creates implementation plan)
       ├─ CTO              (reviews and approves plan)
       ├─ Coder            (implements via TDD)
       ├─ Code Review      (reviews implementation)
       ├─ Security Auditor (audits for vulnerabilities)
       ├─ PR Shepherd      (monitors PR through to merge)
       └─ Knowledge Curator (extracts learnings after merge)
```

- **Swarm Coordinator** — manages multiple issues across parallel worktrees, handles prioritization and conflict detection.
- **Issue Orchestrator** — the main workflow driver. It takes a single GitHub issue through research, planning, implementation, review, and merge.
- **Specialist agents** — do the actual work. Each is spawned by the orchestrator at the appropriate phase.

### The Issue Orchestrator Workflow

The default workflow in `issue-orchestrator.md` has five phases:

| Phase | Agents Involved | What Happens |
|-------|----------------|--------------|
| 1. Analysis | Issue Orchestrator | Read the issue, create a BEADS epic |
| 2. Research & Planning | Researcher, Architect, CTO | Explore codebase, design solution, review plan |
| 3. Implementation | Coder | TDD implementation of the approved plan |
| 4. Review | Code Review, Security Auditor | Parallel review of the implementation |
| 5. PR & Merge | PR Shepherd, Knowledge Curator | Create PR, shepherd to merge, extract learnings |

Tasks flow through a dependency graph — each phase blocks on the previous one completing:

```
Research → Planning → CTO Review → Implementation → Code Review + Security Audit → PR → Merge
```

### Customizing Workflows

#### Removing a Phase

To skip a phase (e.g., security audit on low-risk changes), edit `issue-orchestrator.md` and remove the corresponding task creation and dependency:

```markdown
# Remove these lines from Phase 3:
bd create "Security audit" --type task --parent <epic-id>
bd dep add <security-task> <impl-task>

# And remove the dependency from the PR task:
bd dep add <pr-task> <security-task>   ← delete this
```

#### Adding a New Phase

To add a phase (e.g., a design review step after architecture):

1. Create your agent file (see [Adding a New Agent](#adding-a-new-agent) above).
2. Edit `issue-orchestrator.md` to add a new task and wire it into the dependency graph:

```markdown
# After CTO Review, before Implementation:
bd create "Design review: <feature>" --type task --parent <epic-id>
bd dep add <design-review-task> <cto-review-task>

# Update implementation to depend on design review instead of CTO review:
bd dep add <impl-task> <design-review-task>   ← was <cto-review-task>
```

3. Add the agent spawning logic in the orchestrator, following the existing pattern:

```typescript
Task({
  subagent_type: "general-purpose",
  description: "Design review for issue #123",
  prompt: `You are acting as the DESIGN REVIEWER AGENT for BEADS epic ${epicId}.
  ...
  `,
});
```

#### Running Agents in Parallel

The Issue Orchestrator already runs Code Review and Security Audit in parallel. To parallelize other agents, create tasks without dependencies between them:

```markdown
# These two agents run in parallel (neither depends on the other):
bd create "Code review" --type task --parent <epic-id>
bd create "Security audit" --type task --parent <epic-id>
bd dep add <code-review-task> <impl-task>
bd dep add <security-task> <impl-task>

# The PR task depends on BOTH completing:
bd dep add <pr-task> <code-review-task>
bd dep add <pr-task> <security-task>
```

Any tasks that share the same dependencies but don't depend on each other will run concurrently.

#### Changing Agent Behavior Within a Workflow

Each agent is spawned with a prompt that defines its task. To change what an agent does in the context of a workflow:

1. **Change the agent definition** (in the agent's `.md` file) — affects all workflows that use it.
2. **Change the spawning prompt** (in the orchestrator) — affects only that specific workflow invocation.

For example, to make the Coder agent skip TDD for documentation-only changes, you could either:
- Edit `coder-agent.md` to add a conditional ("if docs-only, skip tests"), or
- Edit the orchestrator's spawning prompt for that specific task type.

### Creating a Custom Workflow

To build an entirely new workflow (e.g., a lightweight "quick fix" flow):

1. Create a new orchestrator agent file:

   ```bash
   touch .claude/plugins/goodtogo/skills/beads/agents/quickfix-orchestrator.md
   ```

2. Define a simpler phase structure:

   ```markdown
   # Quickfix Orchestrator Agent

   **Type**: `quickfix-orchestrator`
   **Role**: Fast-track small fixes without full review cycle
   **Spawned By**: GitHub webhook or manual trigger

   ## Workflow

   ### Phase 1: Analysis
   - Read the issue
   - Verify it's a small, well-scoped fix

   ### Phase 2: Implementation
   - Spawn Coder Agent directly (skip research/architecture)

   ### Phase 3: PR
   - Spawn PR Shepherd
   - Auto-merge if CI passes and fix is trivial
   ```

3. Reference it from the Swarm Coordinator or trigger it directly via a label (e.g., `quickfix-ready` instead of `agent-ready`).

### Swarm Coordination

The Swarm Coordinator (`swarm-coordinator-agent.md`) manages multiple issues running in parallel. Key settings you can customize:

| Setting | Default | What It Controls |
|---------|---------|-----------------|
| `max_concurrent_issues` | 4 | How many issues can be worked on simultaneously |
| `max_worktrees` | 4 | Git worktrees available for parallel work |
| `priority_preemption` | true | Whether P0/P1 issues can pause lower-priority work |
| `conflict_detection` | true | Whether file-level conflicts between issues are detected |

To change these, edit the configuration section in `swarm-coordinator-agent.md` or the `.beads/config.yaml` file.

### Workflow Tips

- **Start simple.** The full 5-phase workflow is designed for non-trivial features. For small fixes, create a lighter orchestrator.
- **Dependencies are the control flow.** The BEADS dependency graph (`bd dep add`) is how you sequence agents. No dependencies = parallel execution.
- **Agents are stateless between spawns.** Each agent invocation starts fresh. Pass all necessary context in the spawning prompt.
- **Test workflow changes on a real issue.** Create a test issue with the `agent-ready` label and watch the orchestrator run through the modified flow.
- **Check the dependency graph.** Use `bd doctor` to detect circular dependencies or orphaned tasks after modifying workflows.

## Security Considerations

When contributing, keep these security principles in mind:

1. **Never log tokens** - Use `<redacted>` in `__repr__`
2. **Validate inputs** - Use `validation.py` functions
3. **Redact errors** - Use `errors.py` for user-facing errors
4. **Secure file permissions** - Cache uses 0600/0700

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/dsifry/goodtogo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dsifry/goodtogo/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
