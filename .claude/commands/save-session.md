---
model: claude-haiku-4-5-20251001
---

# Save Session

Save the current conversation context for future reference and continuation.

## Usage

```
/project:save-session [name]
```

- `name` (optional): Custom name for the session. If not provided, auto-generates from branch name.

## What It Does

Captures and saves the current conversation context including:

1. **Metadata**: Date, branch, repository, custom name
2. **Git State**: Current branch, recent commits, modified files
3. **Work Context**: Open PRs, active todos, recent changes
4. **Conversation Highlights**: Key decisions, code changes, important discussions
5. **Next Steps**: Unfinished tasks and future work

## Session Storage

Sessions are saved to `.claude/sessions/` with the naming format:

```
YYYY-MM-DD-branch-name[-custom-name].md
```

Examples:

- `2024-01-03-feature-auth-system.md`
- `2024-01-03-main-hotfix.md`
- `2024-01-03-feature-payment-stripe-integration.md`

## Features

### Automatic Capture

- Current git branch and status
- Modified files list
- Recent commits (last 10)
- Open pull requests
- Active todos from TodoRead
- Timestamp and duration estimates

### Manual Additions

- Custom session name
- Tags for categorization
- Summary of work completed
- Links to related PRs/issues

### Session File Format

Each session uses YAML frontmatter for metadata and markdown for content:

```yaml
---
id: "2024-01-03-feature-auth-system"
name: "Authentication System Implementation"
date: "2024-01-03T10:30:00Z"
branch: "feature/auth-system"
repo: "dsifry/goodtomerge"
tags: ["auth", "security", "feature"]
summary: "Implemented OAuth2 authentication with Google"
related_prs: [385, 386]
related_commits: ["abc123", "def456"]
---
```

## Examples

### Basic Usage

```
/project:save-session
```

Saves session with auto-generated name based on current branch.

### With Custom Name

```
/project:save-session "OAuth implementation with Google"
```

Saves session with a descriptive custom name.

### After Major Work

```
/project:save-session "Completed user authentication feature"
```

Perfect for capturing the state after finishing a major feature.

## Best Practices

1. **Save regularly**: At natural stopping points or after major decisions
2. **Use descriptive names**: Help your future self understand the context
3. **Save before switching**: Capture context before moving to different work
4. **Include next steps**: Document what needs to be done next

## Related Commands

- `/project:load-session` - Load a previous session
- `/project:list-sessions` - View all saved sessions
- `/project:manage-sessions` - Organize and clean up sessions
- `/project:session-note` - Add quick notes to current session
