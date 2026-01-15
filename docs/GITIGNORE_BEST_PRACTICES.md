# .gitignore Best Practices for GoodToMerge

This guide explains how to properly configure `.gitignore` in your projects when using GoodToMerge with Beads and Claude Code.

## Philosophy: Idempotent Files vs Local State

**Idempotent Files** (COMMIT these):
- Configuration templates that work for everyone
- Workflow definitions (skills, commands, guides)
- Setup instructions
- Files that should be identical across team members

**Local State** (IGNORE these):
- Databases and caches
- Generated files
- User-specific settings
- Runtime artifacts

## Beads Files: What to Commit vs Ignore

### ✅ COMMIT (Idempotent)

```gitignore
# Beads configuration (team-shared settings)
.beads/config.yaml

# Example/template configs for distribution
beads/config.yaml.example
```

**Why?** Config settings like `sync-branch` should be consistent across the team. The example config helps new users get started.

### ❌ IGNORE (Local State)

```gitignore
# Beads local database and state
.beads/                     # Exclude entire directory by default
!.beads/config.yaml         # But allow config.yaml
.beads/beads.db*            # SQLite database (beads.db, beads.db-shm, beads.db-wal)
.beads/issues.jsonl         # Auto-generated from DB (synced via git on beads-sync branch)
.beads/bd.sock              # Daemon socket
.beads/.local_version       # Local version tracking
```

**Why?** These files are:
- **User-specific** - Different for each developer
- **Environment-dependent** - Contains local paths and state
- **Auto-generated** - Created by `bd` commands
- **Synced separately** - `bd sync` handles syncing via the `beads-sync` branch

## Complete .gitignore Template

Here's a comprehensive `.gitignore` for projects using GoodToMerge:

```gitignore
# Python (if using Python)
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
venv/
env/
.venv

# Node.js (if using Node.js)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-store/

# Rust (if using Rust)
target/
Cargo.lock  # Commit for binaries, ignore for libraries

# Go (if using Go)
*.exe
*.test
*.prof
/vendor/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
coverage/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Beads - Task Management
.beads/                     # Exclude directory
!.beads/config.yaml         # Include shared config
.beads/beads.db*            # SQLite database files
.beads/issues.jsonl         # Auto-generated JSONL
.beads/bd.sock              # Daemon socket
.beads/.local_version       # Local version

# Beads Templates (for distribution only)
!beads/config.yaml.example

# Claude Code (optional - usually you want to commit .claude/)
# .claude/sessions/          # Uncomment to ignore saved sessions
# .claude/.cache/            # Uncomment to ignore cache

# Environment & Secrets
.env
.env.local
.env.*.local
*.key
*.pem
*.p12

# Build artifacts
dist/
build/
*.log

# OS files
.DS_Store
Thumbs.db
Desktop.ini
```

## Beads Sync Workflow

Understanding how Beads uses git helps clarify what to ignore:

### 1. Local Work (`.beads/` - gitignored)

```bash
bd create --title="New feature"
bd update beads-123 --status=in_progress
bd close beads-123
```

These commands modify `.beads/beads.db` (gitignored).

### 2. Export to JSONL (auto-generated)

Beads automatically flushes database to `.beads/issues.jsonl` (gitignored).

### 3. Sync to Git (`bd sync`)

```bash
bd sync
```

This:
1. Ensures JSONL is up-to-date
2. **Commits** to `beads-sync` branch (NOT main)
3. **Pushes** to remote

### 4. Team Sync (automatic)

Other team members' Beads daemons:
1. **Pull** from `beads-sync` branch
2. **Import** JSONL to their local database
3. Work continues on their machine

**Key insight**: Issues are synced via the `beads-sync` git branch, NOT by committing `.beads/` files directly.

## Common Mistakes

### ❌ DON'T: Commit `.beads/` Directory

```gitignore
# BAD - This commits database files
# .beads/
```

**Problem**: SQLite database files cause merge conflicts and contain local paths.

### ❌ DON'T: Ignore `.beads/config.yaml`

```gitignore
# BAD - This ignores team configuration
.beads/config.yaml
```

**Problem**: Team members won't have consistent `sync-branch` settings.

### ✅ DO: Selective Ignoring

```gitignore
# GOOD - Ignore directory, allow config
.beads/
!.beads/config.yaml
```

## Project-Specific Considerations

### Multi-Language Projects

Include ignore patterns for ALL languages in your stack:

```gitignore
# Python
__pycache__/
*.pyc

# TypeScript/JavaScript
node_modules/
dist/

# Rust
target/
```

### Monorepos

Use root `.gitignore` for shared tools (Beads, Claude Code), workspace-specific ignores for language-specific artifacts:

```
monorepo/
├── .gitignore              # Beads, Claude Code, OS files
├── python-service/
│   └── .gitignore         # Python-specific
└── rust-service/
    └── .gitignore         # Rust-specific
```

### Private Repositories

You may want to commit Claude Code sessions for team knowledge:

```gitignore
# Don't ignore sessions in private repos
# .claude/sessions/         # Commented out - we want to keep these
```

## Verification

Check your `.gitignore` is working:

```bash
# Should show .beads/config.yaml as tracked
git ls-files .beads/

# Should NOT show database files
git status --ignored | grep beads.db  # Should be listed as ignored

# Verify config is committed
git log --follow -- .beads/config.yaml
```

## Resources

- **Beads Documentation**: [github.com/coderabbitai/beads](https://github.com/coderabbitai/beads)
- **Beads Setup Guide**: [BEADS_SETUP.md](BEADS_SETUP.md)
- **Git Documentation**: [git-scm.com/docs/gitignore](https://git-scm.com/docs/gitignore)

## Quick Reference

```bash
# Files to COMMIT
.beads/config.yaml          # Team configuration
beads/config.yaml.example   # Template for new users
.claude/                    # All Claude Code workflows

# Files to IGNORE
.beads/beads.db*            # SQLite database
.beads/issues.jsonl         # Auto-generated
.beads/bd.sock              # Daemon socket
.beads/.local_version       # Version tracking
.env                        # Secrets
```

---

**Made with Claude Code** 🤖
