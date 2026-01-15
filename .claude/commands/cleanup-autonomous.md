# /project:cleanup-autonomous

> ⚠️ **Note**: `/project:cleanup-autonomous` is a Claude slash command.  
> Type it directly into the chat interface. Attempting to run it in Bash or a
> shell will fail with "no such file or directory".

Clean up artifacts from autonomous mode operation and restore normal settings.

## Usage

```
/project:cleanup-autonomous
```

## Overview

This command helps clean up after autonomous mode by:

- Reviewing and removing backup files
- Restoring normal permission settings
- Consolidating work into proper commits
- Generating final summary report

## Workflow

### 1. List Autonomous Artifacts

```bash
# Find all backup files created during autonomous mode (NUL-delimited for safety)
find . -type f -name "*.backup-*" -not -path "*/node_modules/*" -print0 | xargs -0 ls -la

# Find autonomous working copies
find . -type f -name "*.autonomous-working" -not -path "*/node_modules/*" -print0 | xargs -0 ls -la

# Check for autonomous branches
git branch | grep autonomous-backup
```

### 2. Review Each Backup

For each backup file found:

```bash
# Compare with current version
diff original.ts original.ts.backup-20250624-1430

# If changes were successful, remove backup
rm original.ts.backup-20250624-1430

# If original is better, restore it
mv original.ts.backup-20250624-1430 original.ts
```

### 3. Restore Permission Settings

Remove autonomous mode permissions:

```bash
# Reset settings.local.json to normal state
# Remove autonomous_mode flags and expanded permissions
```

### 4. Consolidate Git History

```bash
# Review all autonomous commits
git log --oneline --grep="autonomous"

# Optionally squash into meaningful commits
git rebase -i <before-autonomous-sha>
```

### 5. Generate Final Report

```markdown
## Autonomous Mode - Final Cleanup Report

**Backup Files Processed**: X

- Removed: Y (changes were successful)
- Restored: Z (reverted to original)

**Git Cleanup**:

- Commits consolidated: A → B
- Branches cleaned: C

**Permissions Reset**: ✅

**Ready for Normal Operation**: ✅
```

## Related Commands

- `/project:autonomous-mode` - Enter autonomous mode
- `/project:review-autonomous` - Review autonomous mode history
