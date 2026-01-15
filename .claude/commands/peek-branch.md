---
description: View a file from another branch without switching context
---

# Peek Branch

View file contents from another branch without changing your working directory.

## Usage

```
/project:peek-branch main src/lib/services/some.service.ts
/project:peek-branch feature/other-pr package.json
```

## Arguments

- `branch` - The branch name to peek into (e.g., `main`, `feature/auth`)
- `file_path` - Path to the file relative to repository root

## Steps

1. **Parse arguments**: Extract branch name and file path from `$ARGUMENTS`

2. **Validate branch exists**:

   ```bash
   git rev-parse --verify "$BRANCH" 2>/dev/null || echo "Branch not found: $BRANCH"
   ```

3. **Show file contents**:

   ```bash
   git show "$BRANCH:$FILE_PATH"
   ```

4. **Optionally show diff** if user wants comparison:
   ```bash
   git diff HEAD.."$BRANCH" -- "$FILE_PATH"
   ```

## Examples

```bash
# View package.json from main branch
/project:peek-branch main package.json

# View a service file from another feature branch
/project:peek-branch feature/new-api src/lib/services/api.service.ts

# Compare current file with main
# (Ask user if they want this after showing the file)
```

## Notes

- This command does NOT switch branches or modify your working directory
- Useful for referencing code from other PRs or seeing what main has
- Works with any valid git ref (branch, tag, commit hash)
