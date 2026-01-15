# Build Validation Guide

This guide covers build processes, validation workflows, and systematic error resolution for the Warmstart codebase.

## Command Timeout Guidelines

**IMPORTANT**: Claude Code has a default 2-minute timeout for Bash commands. For long-running commands, always specify extended timeouts using the `timeout` parameter in milliseconds.

### Recommended Timeouts

| Command                                    | Timeout (ms) | Duration   | Usage                                   |
| ------------------------------------------ | ------------ | ---------- | --------------------------------------- |
| `pnpm build`                               | 300000       | 5 minutes  | Full build with type checking           |
| `pnpm build:validated`                     | 300000       | 5 minutes  | Explicit full validation build          |
| `pnpm build:production`                    | 240000       | 4 minutes  | Production server (skips type checking) |
| `pnpm test --run`                          | 240000       | 4 minutes  | Full test suite execution               |
| `pnpm test:coverage`                       | 300000       | 5 minutes  | Test coverage generation                |
| Database migrations                        | 180000       | 3 minutes  | Large schema changes                    |
| `scripts/test-score-and-draft-pipeline.ts` | 180000       | 3 minutes  | Full AI pipeline testing                |
| Docker builds                              | 600000       | 10 minutes | Container image builds                  |
| Large file processing scripts              | 300000       | 5 minutes  | Bulk data operations                    |

**Note**: Maximum timeout is 600000ms (10 minutes). For operations longer than 10 minutes, break them into smaller steps.

## Faster Build Checks

**Problem**: `pnpm build` runs 3 sequential operations (lint → prisma generate → next build) taking 2-3 minutes total, even when you just need to check for TypeScript errors.

### Quick TypeScript Check Commands

| Command                                | Time     | Purpose                                    |
| -------------------------------------- | -------- | ------------------------------------------ |
| `pnpm typecheck`                       | 5-10s    | Check TypeScript errors only               |
| `pnpm typecheck:watch`                 | Instant  | Continuous TypeScript monitoring           |
| `pnpm check:fast`                      | 15-20s   | Parallel ESLint + TypeScript + tests       |
| `pnpm lint:changed`                    | 1-3s     | Lint only modified files                   |
| `npx tsx scripts/quick-build-check.ts` | Variable | TypeScript check → full build (fails fast) |

### When to Use Each Approach

1. **During Development** → `pnpm typecheck:watch`
   - Keep running in a terminal for instant feedback
   - Catches errors as you type

2. **Before Committing** → `pnpm typecheck` + `pnpm lint:changed`
   - Quick validation of your changes
   - Takes < 15 seconds total

3. **Comprehensive Check** → `pnpm check:fast`
   - Runs ESLint, TypeScript, and test analysis in parallel
   - Provides quality metrics and trends

4. **Before Creating PR** → `npx tsx scripts/quick-build-check.ts`
   - Ensures both TypeScript and full build pass
   - Fails fast on TypeScript errors (saves 2-3 minutes)

5. **Full Production Build** → `pnpm build`
   - Only when you need actual build artifacts
   - Use 300000ms timeout as specified above

### Example Workflow

```bash
# Start development with watch mode
pnpm typecheck:watch

# Before committing, quick check
pnpm typecheck && pnpm lint:changed

# Before PR, ensure everything builds
npx tsx scripts/quick-build-check.ts
```

## Production vs Development Builds

### Overview

The build system supports different optimization strategies for different environments:

| Environment           | Command                                | Type Checking | Use Case                     |
| --------------------- | -------------------------------------- | ------------- | ---------------------------- |
| **Local Development** | `pnpm build`                           | ✅ Full       | Local testing and validation |
| **CI/CD**             | `pnpm build` or `pnpm build:validated` | ✅ Full       | Pre-deployment validation    |
| **Production Server** | `pnpm build:production`                | ⏭️ Skipped    | Fast deploys after CI/CD     |

### Why Skip Type Checking in Production?

**Problem**: Type checking in production builds is redundant when CI/CD already validated types.

**Solution**: Use `SKIP_TYPE_CHECK=true` environment variable to skip type checking on production server.

**Benefits**:

- ⚡ **30-60 seconds faster** production deployments
- ✅ **Same safety** - types validated in CI/CD
- 🎯 **Clear intent** - different commands for different purposes

### Important: When NOT to Skip

**NEVER skip type checking in:**

- ❌ Local development builds
- ❌ CI/CD pipeline builds
- ❌ Before creating PRs
- ❌ When testing type changes

**Why**: Next.js build type checking catches issues that `pnpm typecheck` (tsc --noEmit) may miss, especially:

- Next.js-specific features (route handlers, metadata exports)
- Build-time type generation
- Edge cases in module resolution

### Build Script Details

#### `pnpm build` (Default)

- **Type Checking**: ✅ Full
- **Use**: Local development and CI/CD
- **Script**: `prisma generate && next build`

#### `pnpm build:validated`

- **Type Checking**: ✅ Full (explicit)
- **Use**: CI/CD with clear validation intent
- **Script**: `./scripts/build-with-validation.sh`
- **Features**: Cleans .next, unsets SKIP_TYPE_CHECK

#### `pnpm build:production`

- **Type Checking**: ⏭️ Skipped
- **Use**: Production server ONLY (after CI/CD validation)
- **Script**: `./scripts/build-production-server.sh`
- **Features**: Sets SKIP_TYPE_CHECK=true, cleans .next

### Production Deployment Example

```bash
# On production server (after CI/CD passed)
cd /home/ubuntu/goodtogo
git pull origin main

# Fast production build (types already validated)
pnpm build:production

# Restart application
pm2 restart goodtogo
```

### CI/CD Configuration

```yaml
# GitHub Actions example
steps:
  - name: Build with full validation
    run: pnpm build # OR: pnpm build:validated
    # NO SKIP_TYPE_CHECK environment variable
```

### Environment Variable Control

The build system respects the `SKIP_TYPE_CHECK` environment variable:

```bash
# Development/CI/CD (default - full type checking)
pnpm build

# Production server (skip type checking)
SKIP_TYPE_CHECK=true pnpm build
# OR use convenience script:
pnpm build:production
```

**Configuration**: See `next.config.ts` for `typescript.ignoreBuildErrors` implementation.

## Critical Validation Workflow

**Before marking ANY task complete**, you MUST validate your changes:

1. **TypeScript**: `pnpm tsc --noEmit --project tsconfig.json`
2. **ESLint**: `pnpm eslint <modified-files> --max-warnings 0`
3. **Prettier**: `pnpm prettier --check <modified-files>`

**⚠️ IMPORTANT - Final Validation Before Completion**:
While incremental checks on modified files are useful during development, you MUST run the full validation suite before declaring any task complete:

```bash
# MANDATORY before marking task complete:
pnpm lint          # Full ESLint check - must pass with 0 warnings
pnpm typecheck     # Full TypeScript check - must pass with 0 errors
pnpm build         # Full build - must succeed with no errors
```

**Why**: Your changes may affect other files indirectly through imports, type definitions, or shared utilities. Only a full validation ensures the entire codebase remains healthy.

📋 **Full validation details**: See @.claude/task-completion-checklist.md  
📁 **File tracking guide**: See @.claude/development-workflow.md#file-modification-tracking

## File Tracking for Targeted Validation

**IMPORTANT**: Track all files you modify during a session for efficient validation:

```bash
# Before starting work, check clean state
git status

# During work, periodically check what you've modified
git status --porcelain

# Before validation, get list of modified files (NUL-delimited for safety)
MODIFIED_FILES=$(git diff -z --name-only --diff-filter=ACM | grep -zE '\.(ts|tsx|js|jsx)$')

# Run validation only on YOUR changes
if [ -n "$MODIFIED_FILES" ]; then
  printf '%s' "$MODIFIED_FILES" | xargs -0 pnpm eslint --max-warnings 0
  printf '%s' "$MODIFIED_FILES" | xargs -0 pnpm prettier --check
else
  echo "No modified JS/TS files detected – skipping lint/format."
fi
```

**Why This Matters**:

- Running linters on the entire codebase creates out-of-scope work
- Users expect changes only to files related to the task
- Targeted validation is faster and more focused
- Prevents introducing issues in unrelated code

## Build Error Resolution

**🚨 CRITICAL - DO NOT STOP PREMATURELY**:

- If build errors exist, CONTINUE fixing them
- If tests are failing, CONTINUE debugging
- If ESLint has warnings, CONTINUE resolving them
- The task is NOT complete until ALL validation steps pass

### Systematic Error Fixing Process

1. **Identify ALL errors first**: Run full build and list every error
2. **Group errors by type**: TypeScript, ESLint, test failures
3. **Fix errors systematically**: Start with TypeScript, then ESLint, then tests
4. **Verify each fix**: Re-run build after each batch of fixes
5. **Never skip errors**: Every single error must be resolved

### Common Error Patterns

When encountering build errors:

- **🚨 NEVER USE `as any` OR `@ts-ignore`** - These mask problems instead of solving them
- Don't stop at the first error - use `pnpm build 2>&1 | grep -E "Type error:|Error:"` to see all errors
- After fixing errors, always run the full build again to verify

Common patterns to remember:

- Use `Prisma.JsonNull` instead of `null` for Prisma JSON fields
- Use `Prisma.InputJsonValue` for input, not `Prisma.JsonValue`
- Check property paths carefully (e.g., `profileData.person.positions` not `profileData.positions`)
- Extract nullable values before comparisons (see @.claude/guides/typescript-patterns.md#null-safety-patterns)
- Create proper interfaces instead of using `any`

### Validation Sequence (repeat until ALL pass)

1. Fix all TypeScript errors: `pnpm tsc --noEmit`
2. Fix all ESLint warnings: `pnpm eslint <files> --max-warnings 0`
3. Run tests: `pnpm test --run`
4. Verify build: `pnpm build`
5. If ANY step fails, return to step 1

**Error Continuation Rule**: If you encounter 10 errors, fix ALL 10, not just the first 3

**Success Criteria**: Only mark task complete when build returns exit code 0 with zero errors

## Database & Background Jobs Commands

- `pnpm init-db` - Initialize database
- `pnpm db:seed` - Seed database with initial data
- `pnpm run-job-queue` - Start job queue processor for background tasks
- `pnpm nightly-job-check` - Run maintenance checks
- `pnpm update-tag-counts` - Update tag counts in database

## Onboarding Management Commands

- `pnpm onboarding:status` — Check user onboarding status
- `pnpm onboarding:reset:phase1` — Reset user to Phase 1 (complete restart)
- `pnpm onboarding:reset:phase2` — Reset to Phase 2 (guided tour)
- `pnpm onboarding:reset:phase3` — Reset to Phase 3 (trial extension)
- All onboarding commands support `--dry-run` for safe testing

## See Also

- @.claude/task-completion-checklist.md for detailed completion requirements
- @.claude/guides/typescript-patterns.md for type error resolution
- @.claude/development-workflow.md for file tracking patterns
- @docs/VSCODE_DEBUGGING_SETUP.md for debugging configuration
