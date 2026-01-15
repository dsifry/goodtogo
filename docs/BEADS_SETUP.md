# Beads Installation & Setup Guide

Beads is a git-backed issue tracking system that integrates seamlessly with Claude Code for persistent task management across sessions.

## What is Beads?

Beads provides:

- **Git-backed storage** - Issues stored in `.beads/issues.jsonl`, versioned with git
- **Multi-session persistence** - Track work across Claude Code sessions
- **Dependency management** - Block/depend relationships between issues
- **Rich metadata** - Priority, status, assignees, labels, comments
- **CLI interface** - Fast `bd` commands for issue management
- **Daemon architecture** - Background process for performance

## Installation

### Option 1: npm/pnpm (Recommended)

```bash
# Using npm
npm install -g @coderabbitai/beads

# Using pnpm
pnpm add -g @coderabbitai/beads

# Using yarn
yarn global add @coderabbitai/beads
```

### Option 2: Build from Source

```bash
git clone https://github.com/coderabbitai/beads.git
cd beads
npm install
npm run build
npm link
```

### Verify Installation

```bash
bd --version
```

## Project Setup

### 1. Initialize Beads in Your Repository

```bash
cd /path/to/your/project
bd init
```

This creates:
- `.beads/` directory (add to `.gitignore`)
- `.beads/issues.jsonl` (gitignored, generated from database)
- `.beads/config.yaml` (committed to git)
- `.beads/beads.db` (gitignored, SQLite database)

### 2. Configure Beads

Copy the example config:

```bash
cp beads/config.yaml.example .beads/config.yaml
```

Edit `.beads/config.yaml`:

```yaml
# Set sync branch for team coordination
sync-branch: "beads-sync"

# Auto-start daemon (recommended)
auto-start-daemon: true

# Debounce interval for auto-flush
flush-debounce: "5s"
```

### 3. Set Up Git Integration

Beads uses a dedicated git branch for syncing:

```bash
# Configure sync branch
bd config set sync.branch beads-sync

# Verify
bd config get sync.branch
```

### 4. Add to .gitignore

Ensure your `.gitignore` includes:

```gitignore
# Beads
.beads/
!.beads/config.yaml
```

The database and JSONL files should NOT be committed - only the config.

## Basic Usage

### Creating Issues

```bash
# Create a task
bd create --title="Implement user auth" --type=task --priority=2

# Create a feature
bd create --title="Add dark mode" --type=feature --priority=1

# Create a bug
bd create --title="Fix login redirect" --type=bug --priority=0
```

**Priority levels**: 0 (critical) → 4 (backlog)

### Listing Issues

```bash
# Show ready work (no blockers)
bd ready

# List all open issues
bd list --status=open

# List in-progress work
bd list --status=in_progress

# Show specific issue
bd show beads-123
```

### Updating Issues

```bash
# Start work
bd update beads-123 --status=in_progress

# Assign to someone
bd update beads-123 --assignee=dsifry

# Add label
bd update beads-123 --labels=frontend,urgent

# Change priority
bd update beads-123 --priority=0
```

### Dependencies

```bash
# Make beads-456 depend on beads-123
# (beads-456 is blocked until beads-123 is closed)
bd dep add beads-456 beads-123

# Show blocked issues
bd blocked

# Show what's blocking an issue
bd show beads-456
```

### Completing Work

```bash
# Close issue
bd close beads-123

# Close with reason
bd close beads-123 --reason="Fixed in PR #42"

# Close multiple issues
bd close beads-123 beads-124 beads-125
```

### Syncing with Git

```bash
# Sync to remote (commit + push)
bd sync

# Check sync status
bd sync --status
```

This:
1. Flushes database to `.beads/issues.jsonl`
2. Commits to `beads-sync` branch
3. Pushes to remote

## Integration with GoodToMerge

GoodToMerge includes sophisticated Beads integration:

### Beads Skill

The `beads` skill in `.claude/plugins/goodtomerge/skills/beads/SKILL.md` provides:

- **18 specialized agents** for different task types
- **Automatic context loading** via hooks
- **Session coordination** across multiple agents
- **Knowledge base integration** for lessons learned

### Claude Code Hooks

Add to your project's hooks to auto-load Beads context:

```bash
# .claude/hooks/session-start.sh
#!/bin/bash

# Check for beads
if [ -d ".beads" ]; then
  echo "📋 Beads detected - loading context..."
  bd ready | head -5
  bd list --status=in_progress | head -5
fi
```

### Workflow Integration

1. **Start work**: `bd create` → Claude Code session → `/project:start-task`
2. **Track progress**: TodoWrite for execution, Beads for persistence
3. **Complete**: `/project:create-pr` → `bd close` → `bd sync`

## Advanced Features

### Multi-Repo Support (Experimental)

Track issues across multiple repos:

```yaml
# .beads/config.yaml
repos:
  primary: "."
  additional:
    - ~/personal-planning
    - ~/work-planning
```

### Custom Issue Prefix

```yaml
# .beads/config.yaml
issue-prefix: "myproject"
```

Creates issues like `myproject-1`, `myproject-2`, etc.

### No-DB Mode

Use JSONL directly without SQLite:

```yaml
# .beads/config.yaml
no-db: true
```

Slower but simpler for small projects.

### GitHub/Jira/Linear Integration

```bash
# Set GitHub integration
bd config set github.org myorg
bd config set github.repo myrepo

# Set Jira integration
bd config set jira.url https://mycompany.atlassian.net
bd config set jira.project PROJ

# Set Linear integration
bd config set linear.url https://linear.app/team
bd config set linear.api-key <key>
```

## Troubleshooting

### Daemon Won't Start

```bash
# Check status
bd doctor

# Manually start daemon
bd daemon start

# Check logs
tail -f ~/.beads/daemon.log
```

### Sync Conflicts

```bash
# Force import from JSONL
bd import --force

# Force export to JSONL
bd flush --force
```

### Database Corruption

```bash
# Rebuild from JSONL
rm .beads/beads.db
bd import
```

### Performance Issues

```bash
# Disable daemon (direct DB access)
bd config set no-daemon true

# Reduce flush debounce
bd config set flush-debounce 1s
```

## Best Practices

1. **Use `bd sync` regularly** - Keep team in sync
2. **Set priorities consistently** - 0=critical, 2=medium, 4=backlog
3. **Track dependencies** - Block work that depends on others
4. **Close with reasons** - Document why issues closed
5. **Use labels** - Organize by feature/component
6. **Check `bd ready`** - Focus on unblocked work
7. **Multi-session work → Beads** - TodoWrite for single session

## Resources

- **Official Docs**: [github.com/coderabbitai/beads](https://github.com/coderabbitai/beads)
- **GoodToMerge Beads Skill**: `.claude/plugins/goodtomerge/skills/beads/SKILL.md`
- **Example Config**: `beads/config.yaml.example`

## Quick Reference

```bash
# Common Commands
bd create --title="..." --type=task --priority=2
bd ready
bd list --status=open
bd update <id> --status=in_progress
bd close <id>
bd sync

# Dependencies
bd dep add <issue> <depends-on>
bd blocked

# Info
bd show <id>
bd stats
bd doctor
```

---

**Made with Claude Code** 🤖
