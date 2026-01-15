# CLAUDE.md

This file provides guidance to Claude Code when working with the Good To Go repository.

## Overview

Good To Go is a **language-neutral** Claude Code workflow system. This project is written in Python, but the workflows and skills work with any programming language.

## Essential Commands

**Build & Test** (Python-specific for this project):

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Format
black .

# Type check
mypy src/
```

**Quality Checks Before Completing Tasks:**

```bash
pytest && ruff check . && black --check . && mypy src/
```

## Core Workflows

### PR Shepherd

Monitor PRs through to merge with `/project:pr-shepherd [pr-number]`

Auto-activates to:
- Watch CI/CD status
- Handle review comments
- Auto-fix issues
- Resolve threads
- Notify when ready

### Handle PR Comments

Address code review feedback systematically with `/project:handle-pr-comments <pr-number>`

Ensures:
- All threads addressed
- Proper attribution
- Thread resolution
- Comprehensive fixes

### Task Management (Beads)

Track work across sessions:

```bash
bd create --title="Feature X" --type=feature --priority=2
bd ready                    # Show available work
bd update <id> --status=in_progress
bd close <id>              # Mark complete
bd sync                    # Sync with git
```

### Session Management

Save/resume context:

```
/project:save-session <name>
/project:load-session <identifier>
/project:list-sessions
```

## Custom Slash Commands

All commands are in `.claude/commands/`:

| Command | Purpose |
|---------|---------|
| `/project:start-task` | Task assessment |
| `/project:create-issue` | Create GitHub issue with agent instructions |
| `/project:create-pr` | Create comprehensive PR |
| `/project:pr-shepherd` | Monitor PR to merge |
| `/project:handle-pr-comments` | Address review feedback |
| `/project:review-this` | CTO-level spec review |
| `/project:production-mode` | Production safety protocol |
| `/project:save-session` | Save context |
| `/project:load-session` | Resume session |
| `/project:worktree-create` | Create parallel workspace |
| `/project:worktree-status` | Show worktree context |

See all: `.claude/commands/`

## Good To Go Skills (Auto-Activate)

Skills in `.claude/plugins/goodtogo/skills/` auto-activate based on context:

| Skill | When It Activates |
|-------|-------------------|
| `goodtogo:pr-shepherd` | After PR creation or on-demand |
| `goodtogo:handling-pr-comments` | When addressing PR feedback |
| `goodtogo:create-issue` | Creating comprehensive GitHub issues |
| `goodtogo:posthog-analytics` | When querying analytics (if configured) |

## Git Workflow

**Branch Naming**: `feat/`, `fix/`, `docs/`, `refactor/`, `chore/`

**Commit Messages**:
- Concise, present tense
- Include `🤖 Generated with Claude Code` when appropriate
- Follow conventional commits style

**PR Process**:
1. Create branch
2. Make changes
3. Create PR with `/project:create-pr`
4. Monitor with `/project:pr-shepherd`
5. Merge when ready

## Critical Guidelines

- **NEVER commit directly to main** - Use PR workflow
- **ALWAYS run tests before PR** - Ensure quality
- **Use Beads for multi-step work** - Track across sessions
- **Save sessions for complex work** - Resume context later
- **Check branch before git ops** - `git branch --show-current`

## Worktree Development

For parallel development:

```bash
/project:worktree-create my-feature feat/my-feature
/project:worktree-status
```

All worktrees share the same database - coordinate schema changes.

## Documentation Structure

```
.claude/
├── commands/           # All slash commands
├── guides/            # Workflow guides
│   ├── git-workflow.md
│   ├── todo-management.md
│   ├── session-management.md
│   └── worktree-development.md
└── plugins/goodtogo/
    └── skills/        # Auto-activating skills
        ├── pr-shepherd/
        ├── handling-pr-comments/
        ├── create-issue/
        └── beads/
```

## Language-Neutral Design

Good To Go workflows are designed to work with **any language**:

- Commands use generic terms (BUILD, TEST, LINT)
- Skills adapt to project context
- No hardcoded language assumptions
- Task management is universal

When adapting to your project, update this file with your specific build/test commands.

## Development Philosophy

1. **Simple & Concise** - Clear over complex
2. **Language-Neutral** - Works everywhere
3. **Workflow-Focused** - Git/PR excellence
4. **Task Persistence** - Beads for continuity
5. **Community-Driven** - Open and extensible

## Extended Thinking

For complex tasks, use: `think`, `think hard`, `think harder`, or `ultrathink`

## Important Reminders

- Ask when unclear - better to clarify than assume
- Track todos with TodoWrite for multi-step tasks
- Include `🤖 Generated with Claude Code` in commits
- Use `/project:cleanup-files` to remove unnecessary files
- Check for existing skills before creating new ones

---

**Made with Claude Code** 🤖
