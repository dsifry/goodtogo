---
model: claude-haiku-4-5-20251001
---

# /project:format-code

Format code files using prettier with project defaults before committing changes.

## Usage

```bash
/project:format-code [file-path or pattern]
```

## Examples

```
# Format a single file
/project:format-code src/components/Button.tsx

# Format all TypeScript files in a directory
/project:format-code "src/components/**/*.ts"

# Format all modified files
/project:format-code --staged
```

## What This Command Does

1. **Identifies files to format** based on the provided path or pattern
2. **Runs prettier** with project configuration
3. **Shows formatting results** and any files that were changed
4. **Optionally runs linting** to ensure code quality

## Format Patterns

### Single File

```bash
pnpm prettier --write <file-path>
```

### Multiple Files by Pattern

```bash
pnpm prettier --write "src/**/*.{ts,tsx,js,jsx}"
```

### Check Without Modifying

```bash
pnpm prettier --check <file-path>
```

### Format Staged Files Only

```bash
# Get list of staged files
git diff --cached --name-only | grep -E '\.(ts|tsx|js|jsx)$' | xargs pnpm prettier --write
```

## When to Use

- **Before committing** any new or modified code
- **After generating** new files with Claude
- **When resolving** merge conflicts
- **After refactoring** existing code

## Project Prettier Configuration

The project uses the following prettier defaults (defined in `.prettierrc`):

- Print width: 100 characters
- Tab width: 2 spaces
- Semi-colons: true
- Single quotes: false
- Trailing commas: ES5
- Bracket spacing: true
- Arrow parens: avoid
- End of line: auto

## Additional Checks

After formatting, run linting on files you've created or modified:

### Linting Strategy

**For files we create or modify**: Fix both errors AND warnings to gradually improve code quality:

```bash
# Check specific file we're working on (zero warnings tolerance)
pnpm eslint <file-path> --max-warnings=0

# Auto-fix what's possible on our file
pnpm eslint <file-path> --fix --max-warnings=0

# Check only staged files before commit
git diff --cached --name-only | grep -E '\.(ts|tsx|js|jsx)$' | xargs pnpm eslint --max-warnings=0
```

### TypeScript Type Checking

```bash
# Run TypeScript compiler checks (no emit, just type checking)
pnpm tsc --noEmit

# Note: TypeScript checking also runs during `pnpm build`
```

**When you encounter TypeScript warnings/errors**:

- **Fix them properly** - don't use workarounds like `as any` or `as unknown as Type`
- Define proper interfaces and types for all data structures
- For mocks: Create properly typed mocks with all required properties
- For API responses: Define interfaces that match the actual response shape
- For function parameters: Use specific types or generics, never `any`
- Use `ReturnType<typeof fn>` and `Awaited<T>` for dynamic types
- Reference [TESTING_STRATEGY.md](../../docs/TESTING_STRATEGY.md#type-safety-best-practices) for complex mock patterns

### Important Notes

- **CI/CD**: Uses `--max-warnings=999999` (only fails on errors)
- **Our approach**: Fix warnings ONLY in files we're creating/modifying
- **Avoid yak shaving**: Don't touch warnings in existing files unless already working on them
- **Type safety**: When fixing type warnings, follow proper TypeScript patterns, not quick `any` fixes

## Tips

1. **VS Code Integration**: Install the Prettier extension for automatic formatting on save
2. **Pre-commit Hook**: The project may have husky hooks that auto-format staged files
3. **CI/CD**: Formatting is checked in CI, so always format before pushing

## Common Issues

### File Not Found

Ensure the file path is relative to the project root.

### Prettier Not Found

Run `pnpm install` to ensure prettier is installed.

### Configuration Conflicts

Check for `.prettierrc` or `prettier` config in package.json for project-specific rules.
