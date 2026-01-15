---
model: claude-haiku-4-5-20251001
---

# Cleanup Claude Files

Remove unnecessary Claude-generated files while preserving important documentation and configurations.

## Usage

```
/project:cleanup-files
```

## Steps

1. **Review MANAGED_FILES.md** - Check the current list of files to preserve
2. **Audit current files** - Find all Claude-related files in the project
3. **Identify cleanup candidates** - Files not listed in MANAGED_FILES.md
4. **Confirm with user** - Before deleting, show what will be removed
5. **Clean up safely** - Remove only confirmed unnecessary files
6. **Update MANAGED_FILES.md** - Remove any cleaned up files from temporary section

## Safety Checks

- Never delete files listed in MANAGED_FILES.md "Preserve Always" sections
- Always confirm before deleting any files
- Show file contents for review if uncertain about deletion
- Suggest moving questionable files to temporary section instead of deleting

## Commands to Run

```bash
# Find all Claude-related files
find . -name "*claude*" -o -path "*/.claude/*" | grep -v node_modules

# Show files not in git (potential cleanup candidates)
git status --porcelain | grep "^??"
```
