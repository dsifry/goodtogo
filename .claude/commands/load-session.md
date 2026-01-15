---
model: claude-haiku-4-5-20251001
---

# Load Session

Load a previously saved conversation session to continue where you left off.

## Usage

```
/project:load-session [identifier]
```

- `identifier`: Can be:
  - Session ID (e.g., `2024-01-03-feature-auth`)
  - Partial name match (e.g., `auth`)
  - Date (e.g., `2024-01-03`)
  - Branch name (e.g., `feature/auth-system`)
  - Tag (e.g., `#security`)

If multiple sessions match, you'll be prompted to select one.

## What It Does

1. **Searches** for matching sessions based on your identifier
2. **Displays** matching sessions with summaries
3. **Loads** the selected session context
4. **Shows**:
   - Session overview and summary
   - Current branch vs. session branch
   - Open todos and next steps
   - Recent context and decisions
   - File modifications from that session

## Search Methods

### By ID (Exact Match)

```
/project:load-session 2024-01-03-feature-auth-system
```

### By Name (Partial Match)

```
/project:load-session "OAuth implementation"
```

### By Date (All from Date)

```
/project:load-session 2024-01-03
```

Shows all sessions from January 3, 2024.

### By Branch

```
/project:load-session feature/auth-system
```

Shows all sessions from the specified branch.

### By Tag

```
/project:load-session #security
```

Shows all sessions tagged with "security".

### Interactive Mode

```
/project:load-session
```

Without identifier, shows recent sessions for selection.

## Session Display Format

When loading a session, you'll see:

```
📋 SESSION: OAuth implementation with Google
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: 2024-01-03 10:30 AM
🌿 Branch: feature/auth-system (current: main)
🏷️  Tags: auth, security, feature
📝 Summary: Implemented OAuth2 authentication with Google

⚠️  Branch Mismatch: Session was on 'feature/auth-system', currently on 'main'

📄 Modified Files (5):
  • src/auth/google-oauth.ts
  • src/components/LoginForm.tsx
  • .env.example
  • package.json
  • src/lib/auth-helpers.ts

✅ Completed Tasks:
  • Set up Google OAuth credentials
  • Implemented callback handler
  • Created login UI component

📌 Next Steps:
  • Add error handling for failed auth
  • Implement logout functionality
  • Add session persistence

🔗 Related:
  • PR #385: Add Google OAuth authentication
  • Commits: abc123, def456, ghi789
```

## Options

### Load and Switch Branch

If on a different branch, you'll be asked:

```
Session was on branch 'feature/auth-system' but you're on 'main'.
Would you like to:
1. Switch to feature/auth-system
2. Stay on main
3. View diff between branches
```

### Recent Context

Automatically shows:

- Last 5 commits from the session
- Key code blocks discussed
- Important decisions made

## Examples

### Load Most Recent

```
/project:load-session
```

Shows last 5 sessions for interactive selection.

### Load by Partial Name

```
/project:load-session auth
```

Finds all sessions with "auth" in the name.

### Load Today's Sessions

```
/project:load-session today
```

Special keyword to show all sessions from today.

### Load by Multiple Criteria

```
/project:load-session "2024-01-03 #bugfix"
```

Sessions from Jan 3, 2024 tagged as bugfix.

## Best Practices

1. **Check branch alignment**: Ensure you're on the right branch
2. **Review next steps**: Pick up where you left off
3. **Check related PRs**: See if they've been merged or need updates
4. **Verify file states**: Ensure files still exist and match expectations

## Related Commands

- `/project:save-session` - Save current context
- `/project:list-sessions` - Browse all sessions
- `/project:manage-sessions` - Delete or archive sessions
- `/project:session-note` - Add notes to current session
