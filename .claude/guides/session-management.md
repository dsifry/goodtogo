# Session Management Guide

This guide explains how to use the session management system to preserve conversation context across Claude Code sessions.

## Overview

The session management system allows you to:

- Save your current conversation context with important decisions, code changes, and next steps
- Load previous sessions to continue where you left off
- Search and browse through past sessions
- Organize sessions with tags, branches, and custom names

## Quick Start

### Save Current Session

```
/project:save-session "Implementing OAuth with Google"
```

### Load Previous Session

```
/project:load-session auth
```

### List Recent Sessions

```
/project:list-sessions --recent 5
```

## Session Structure

Sessions are stored in `.claude/sessions/` with metadata and content:

```yaml
---
id: "2024-01-03-feature-auth-oauth-implementation"
name: "OAuth implementation with Google"
date: "2024-01-03T10:30:00Z"
branch: "feature/auth-system"
tags: ["auth", "oauth", "google", "security"]
summary: "Implemented Google OAuth2 authentication"
related_prs: [385, 386]
---
# Session Content
[Conversation context, decisions, code changes, etc.]
```

## Naming Conventions

### Automatic ID Generation

Format: `YYYY-MM-DD-branch-name[-custom-name]`

Examples:

- `2024-01-03-main` - Simple session on main branch
- `2024-01-03-feature-payments` - Feature branch session
- `2024-01-03-feature-payments-stripe-integration` - With custom name

### Best Practices for Names

- Use descriptive names that explain the work
- Include key technology or component names
- Keep names concise but meaningful

## Search and Filter

### Search by Content

```
/project:list-sessions --search "PostHog configuration"
/project:list-sessions --search "setupPostHog()"
```

### Filter by Branch

```
/project:list-sessions --branch feature/auth-system
/project:list-sessions --branch main --recent 10
```

### Filter by Date

```
/project:list-sessions --date today
/project:list-sessions --date 2024-01-03
/project:list-sessions --date this-week
```

### Filter by Tags

```
/project:list-sessions --tag bugfix
/project:list-sessions --tag security --tag urgent
```

## Session Workflow

### 1. Starting Work

```
# Check for previous related sessions
/project:list-sessions --branch current

# Load if continuing previous work
/project:load-session previous-session-id
```

### 2. During Work

```
# Capture learnings in real-time (when you discover something non-obvious)
/project:til "Thread model is for drafts only, not email threads - despite the name"

# Add quick notes to current session
/project:session-note "Decision: Use Redis for session storage"

# Save at natural breakpoints
/project:save-session "Completed Redis integration"
```

**Real-Time Knowledge Capture**: When you discover something that would confuse a naive agent, capture it immediately with `/project:til`. This stores the learning in `.beads/knowledge/` with proper provenance.

### 3. Ending Work

```
# IMPORTANT: Extract learnings BEFORE saving session
/project:extract-learnings  # Mine conversation for implicit insights

# Save comprehensive session
/project:save-session "Auth system - ready for review"

# The session captures:
# - All modified files
# - Key decisions made
# - Code snippets discussed
# - Open todos
# - Next steps
# - Extracted learnings (stored in .beads/knowledge/)
```

**Knowledge Capture Workflow**: Before ending a session, run `/project:extract-learnings` to identify insights that would help future agents. This analyzes your conversation for debugging discoveries, architectural decisions, and non-obvious behaviors.

### 4. Resuming Work

```
# Next day/session
/project:load-session yesterday

# Shows:
# - What you were working on
# - Current vs session branch
# - Files modified
# - Next steps to continue
```

## Advanced Features

### Session Templates

Different templates for different work types:

- **default-template.md** - General development work
- **bug-fix-template.md** - Bug investigation and fixes
- **feature-template.md** - Feature implementation

### Session Linking

Sessions can reference each other:

```yaml
related_sessions:
  - previous: "2024-01-02-feature-auth-setup"
  - related: "2024-01-03-feature-auth-testing"
```

### Current Session

A symlink at `.claude/CURRENT_SESSION.md` always points to the active session, making it easy to:

- Add notes manually
- Reference in other tools
- Track what you're working on

### Session Archive

Old sessions can be archived to keep the main list clean:

```
/project:manage-sessions archive --older-than 30d
```

Archived sessions move to `.claude/sessions/archive/YYYY/MM/`

## Integration with Git Workflow

### Pre-Commit Hook

Consider saving session before major commits:

```
/project:save-session "Pre-commit: <commit-message>"
```

### Branch Switching

Save session before switching branches:

```
/project:save-session "Switching to work on hotfix"
git checkout main
```

### PR Creation

Sessions automatically link to PRs when created:

```
/project:create-pr
# Session will include PR number in metadata
```

## Integration with BEADS Knowledge Base

The knowledge capture system integrates with BEADS to ensure learnings are preserved for future agents.

### Knowledge Capture Commands

| Command                             | When to Use                                         | What It Does                                       |
| ----------------------------------- | --------------------------------------------------- | -------------------------------------------------- |
| `/project:til <learning>`           | During work, when discovering something non-obvious | Captures a single learning with conflict detection |
| `/project:extract-learnings`        | End of session, before saving                       | Mines conversation history for implicit insights   |
| `/project:curate-pr-learnings <pr>` | After PR merge (via PR Shepherd Phase 7)            | Extracts learnings from CodeRabbit comments        |

### Knowledge Sources Hierarchy

1. **Real-time TIL** (highest signal) - Explicit captures during work
2. **Session extraction** - Mining conversation for implicit insights
3. **PR curation** - CodeRabbit and human review comments
4. **Agent discoveries** - Learnings from debugging and implementation

### Session Close Checklist (Knowledge-Aware)

Before ending a significant work session:

```bash
# 1. Capture any remaining learnings
/project:extract-learnings

# 2. Save session context
/project:save-session "Description"

# 3. Sync BEADS state
bd sync

# 4. Push to remote
git push
```

### Querying Knowledge Before Work

When starting a task, query relevant learnings:

```bash
# Search for relevant knowledge
pnpm tsx scripts/knowledge-base.ts search --query "gmail api rate limiting"

# Check all knowledge for a service
pnpm tsx scripts/knowledge-base.ts list --type api_behavior
```

### Knowledge Storage

Learnings are stored in `.beads/knowledge/`:

- `codebase-facts.jsonl` - How the code works
- `api-behaviors.jsonl` - External API quirks
- `patterns.jsonl` - Reusable patterns
- `gotchas.jsonl` - Common pitfalls
- `decisions.jsonl` - Architectural decisions

## Tips and Tricks

### 1. Consistent Tagging

Use consistent tags for easy filtering:

- `#bugfix` - Bug fixes
- `#feature` - New features
- `#refactor` - Code refactoring
- `#urgent` - High priority work
- `#research` - Investigation/exploration

### 2. Session Chains

For multi-day features, create linked sessions:

- Day 1: `auth-system-setup`
- Day 2: `auth-system-implementation`
- Day 3: `auth-system-testing`

### 3. Quick Context Switch

When interrupted:

```
/project:save-session "WIP: Debugging auth issue"
# Work on urgent task
/project:load-session WIP
```

### 4. Session Reviews

Weekly review of work:

```
/project:list-sessions --date this-week --stats
```

### 5. Knowledge Base

Search past sessions for solutions:

```
/project:list-sessions --search "similar error"
/project:list-sessions --search "redis connection"
```

## Troubleshooting

### Session Not Found

If load-session can't find your session:

1. Check exact ID: `/project:list-sessions`
2. Try partial match: `/project:load-session partial-name`
3. Check if archived: Look in `.claude/sessions/archive/`

### Merge Conflicts

If session files have conflicts:

1. Sessions are markdown - resolve like any text file
2. Keep both versions if unsure
3. Use `/project:manage-sessions merge` to combine

### Storage Management

If running low on space:

```
/project:manage-sessions cleanup --remove-empty
/project:manage-sessions archive --older-than 60d
```

## Session Management Commands Reference

- **save-session** - Save current context
- **load-session** - Load previous session
- **list-sessions** - Browse and search sessions
- **manage-sessions** - Archive, delete, merge sessions
- **session-note** - Add quick note to current session (future feature)

## Best Practices Summary

1. **Save Often**: At natural stopping points
2. **Name Clearly**: Future you will thank you
3. **Tag Consistently**: Makes searching easier
4. **Link Related Work**: Connect multi-session features
5. **Archive Regularly**: Keep active list manageable
6. **Review Weekly**: Learn from past sessions

---

The session management system helps maintain continuity across your Claude Code conversations, making it easier to work on complex, long-running projects without losing context.
