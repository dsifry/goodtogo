---
model: claude-haiku-4-5-20251001
---

# List Sessions

Browse and search through all saved conversation sessions.

## Usage

```
/project:list-sessions [options]
```

## Options

- `--branch <name>` - Filter by branch name
- `--tag <tag>` - Filter by tag
- `--date <date>` - Filter by date (YYYY-MM-DD or relative like "today", "yesterday", "this-week")
- `--recent <n>` - Show last N sessions (default: 10)
- `--search <query>` - Full-text search across sessions
- `--stats` - Show session statistics

## Display Format

Sessions are displayed in a table format:

```
📋 SAVED SESSIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ID                                    | Date       | Branch              | Name                        | Tags
────────────────────────────────────┼────────────┼────────────────────┼────────────────────────────┼──────────
2024-01-03-feature-auth-system      | 2024-01-03 | feature/auth-system | OAuth implementation       | auth, security
2024-01-02-main-hotfix              | 2024-01-02 | main               | Critical bug fix           | bugfix, urgent
2024-01-02-feature-payment          | 2024-01-02 | feature/payment    | Stripe integration         | payment, feature
2024-01-01-refactor-api             | 2024-01-01 | refactor/api-v2    | API restructuring          | refactor, breaking

Total: 4 sessions | Current branch: main
```

## Filter Examples

### Recent Sessions

```
/project:list-sessions --recent 5
```

Shows the 5 most recent sessions.

### By Branch

```
/project:list-sessions --branch feature/auth-system
```

Shows all sessions from the auth-system feature branch.

### By Date

```
/project:list-sessions --date today
/project:list-sessions --date 2024-01-03
/project:list-sessions --date this-week
```

### By Tag

```
/project:list-sessions --tag bugfix
/project:list-sessions --tag security
```

### Combined Filters

```
/project:list-sessions --branch main --tag bugfix --recent 10
```

Shows last 10 bugfix sessions from main branch.

## Search Functionality

### Full-Text Search

```
/project:list-sessions --search "OAuth implementation"
/project:list-sessions --search "PostHog"
```

Searches through session content, not just metadata.

### Code Search

```
/project:list-sessions --search "setupPostHog()"
/project:list-sessions --search "import.*PostHog"
```

Find sessions where specific code was discussed.

### File Search

```
/project:list-sessions --search "modified:auth-helpers.ts"
/project:list-sessions --search "file:*.test.ts"
```

## Statistics View

```
/project:list-sessions --stats
```

Shows:

```
📊 SESSION STATISTICS
━━━━━━━━━━━━━━━━━━━━
Total Sessions: 47
This Week: 12
This Month: 31

By Branch:
  main: 15 sessions
  feature/*: 28 sessions
  bugfix/*: 4 sessions

By Tag:
  feature: 23
  bugfix: 12
  refactor: 8
  security: 4

Most Active Days:
  Monday: 14 sessions
  Tuesday: 10 sessions
  Friday: 9 sessions

Average Session Duration: ~2.5 hours
Total Commits Referenced: 234
Total PRs Created: 18
```

## Interactive Features

### Quick Actions

After listing, you can:

- Type a number to load that session
- Type 'd' to delete a session
- Type 'a' to archive old sessions
- Type 'q' to quit

### Sorting

Default sort is by date (newest first). Can change with:

- `--sort date-asc` - Oldest first
- `--sort name` - Alphabetical by name
- `--sort branch` - Group by branch

### Export

```
/project:list-sessions --export sessions-backup.json
```

Exports session metadata for backup or analysis.

## Special Keywords

- `today` - Sessions from today
- `yesterday` - Sessions from yesterday
- `this-week` - Current week's sessions
- `last-week` - Previous week's sessions
- `this-month` - Current month's sessions

## Examples

### Daily Standup View

```
/project:list-sessions --date today --stats
```

See what you worked on today with statistics.

### Branch Cleanup

```
/project:list-sessions --branch feature/old-feature
```

Find sessions from old branches before cleanup.

### Weekly Review

```
/project:list-sessions --date this-week --stats
```

Review the week's work and progress.

## Related Commands

- `/project:save-session` - Save current session
- `/project:load-session` - Load a specific session
- `/project:manage-sessions` - Delete, archive, or merge sessions
- `/project:session-note` - Add notes to current session
