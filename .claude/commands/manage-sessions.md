---
model: claude-haiku-4-5-20251001
---

# Manage Sessions

Organize, archive, and maintain your saved conversation sessions.

## Usage

```
/project:manage-sessions [action] [options]
```

## Actions

### Archive Sessions

Move old sessions to the archive folder:

```
/project:manage-sessions archive --older-than 30d
/project:manage-sessions archive --branch deleted-branch
/project:manage-sessions archive --ids session1,session2,session3
```

### Delete Sessions

Permanently remove sessions:

```
/project:manage-sessions delete --id 2024-01-03-old-session
/project:manage-sessions delete --branch feature/abandoned
/project:manage-sessions delete --older-than 90d --archived
/project:manage-sessions delete --id 2024-01-03-old-session --yes  # Skip confirmation
```

### Merge Sessions

Combine related sessions:

```
/project:manage-sessions merge --ids session1,session2 --name "Combined OAuth work"
/project:manage-sessions merge --branch feature/auth --name "Auth implementation"
```

### Clean Up

Remove duplicate or empty sessions:

```
/project:manage-sessions cleanup
/project:manage-sessions cleanup --dry-run
```

### Export/Import

Backup and restore sessions:

```
/project:manage-sessions export --output sessions-backup.json
/project:manage-sessions import --input sessions-backup.json
```

## Interactive Mode

Running without arguments starts interactive mode:

```
/project:manage-sessions
```

Shows menu:

```
📋 SESSION MANAGEMENT
━━━━━━━━━━━━━━━━━━━

Current Status:
  Active Sessions: 23
  Archived Sessions: 45
  Total Size: 2.3 MB

What would you like to do?
1. Archive old sessions
2. Delete sessions
3. Merge related sessions
4. Clean up duplicates
5. Export sessions
6. View statistics
7. Exit

Enter choice:
```

## Archive Management

### Auto-Archive Rules

Set up automatic archiving:

```
/project:manage-sessions auto-archive --setup
```

Configure rules like:

- Archive sessions older than 30 days
- Archive sessions from deleted branches
- Archive sessions from merged PRs

### Archive Structure

Archived sessions are moved to:

```
.claude/sessions/archive/YYYY/MM/
```

Example:

```
.claude/sessions/archive/2024/01/2024-01-03-feature-old.md
```

### Restore from Archive

```
/project:manage-sessions restore --id 2024-01-03-feature-old
/project:manage-sessions restore --all-from-branch feature/revived
```

## Cleanup Operations

### Find Duplicates

```
/project:manage-sessions cleanup --show-duplicates
```

Identifies sessions that:

- Have the same content but different names
- Were saved multiple times in quick succession
- Have minimal content changes

### Remove Empty Sessions

```
/project:manage-sessions cleanup --remove-empty
```

Removes sessions that:

- Have no meaningful content
- Were created but never updated
- Only contain template text

### Optimize Storage

```
/project:manage-sessions optimize
```

- Compresses session content
- Removes redundant metadata
- Consolidates similar sessions

## Merge Strategies

### By Branch

Merge all sessions from a feature branch:

```
/project:manage-sessions merge --branch feature/big-feature --strategy chronological
```

### By Time Range

Merge sessions from a specific period:

```
/project:manage-sessions merge --date-range 2024-01-01:2024-01-07 --name "Week 1 Sprint"
```

### By Tag

Merge sessions with common tags:

```
/project:manage-sessions merge --tag bugfix --tag urgent --name "Critical fixes"
```

### Merge Options

- `--strategy chronological` - Order by date
- `--strategy topic` - Group by similarity
- `--preserve-originals` - Keep source sessions
- `--interactive` - Review before merging

## Export Options

### Full Export

```
/project:manage-sessions export --all --format json
```

### Selective Export

```
/project:manage-sessions export --branch main --format markdown
/project:manage-sessions export --tag important --format json
/project:manage-sessions export --recent 30d --format csv
```

### Export Formats

- `json` - Full metadata and content
- `markdown` - Readable markdown files
- `csv` - Metadata only for analysis
- `zip` - Compressed archive

## Statistics and Reports

```
/project:manage-sessions stats [period]
```

Shows detailed statistics:

```
📊 SESSION STATISTICS - Last 30 Days
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sessions Created: 45
Sessions Archived: 12
Total Size: 3.2 MB

Most Active:
  Branch: feature/auth-system (12 sessions)
  Day: Tuesday (8 sessions average)
  Time: 2-4 PM (15 sessions)

Session Duration:
  Average: 2h 15m
  Longest: 5h 30m (2024-01-15-refactor-api)
  Shortest: 15m (2024-01-20-main-typo-fix)

Content Stats:
  Total Lines: 12,453
  Code Blocks: 234
  Decisions Made: 89
  TODOs Created: 156
  PRs Referenced: 23

Top Tags:
  1. feature (23)
  2. bugfix (15)
  3. refactor (8)
```

## Best Practices

1. **Regular Cleanup**: Run cleanup monthly to maintain organization
2. **Archive Before Delete**: Archive sessions before permanently deleting
3. **Meaningful Merges**: Only merge truly related sessions
4. **Backup Important Work**: Export sessions before major cleanups
5. **Use Tags**: Tag sessions during save for easier management

## Safety Features

- **Dry Run Mode**: Preview changes before executing
- **Confirmation Prompts**: Require confirmation for destructive actions
- **Undo Support**: Recent deletions can be recovered from trash
- **Backup Reminder**: Prompts to backup before bulk operations

## Related Commands

- `/project:save-session` - Save current session
- `/project:load-session` - Load a session
- `/project:list-sessions` - Browse sessions
- `/project:session-note` - Add notes to current session
