# Parallel Type Fix Command

## Overview

This command systematically finds all TypeScript and ESLint errors across the codebase, distributes the work across parallel subagents, and provides real-time progress tracking. Each agent fixes type issues in parallel since they are independent file-based changes.

## Usage

```
/project:parallel-type-fix [options]
```

### Options

- `--agents=N` - Number of parallel agents (default: 5, max: 10)
- `--focus=typescript|eslint|both` - Type of errors to focus on (default: both)
- `--dry-run` - Show what would be done without making changes
- `--verbose` - Show detailed progress and error information

### Examples

```
/project:parallel-type-fix
/project:parallel-type-fix --agents=8 --focus=typescript
/project:parallel-type-fix --dry-run --verbose
```

## Implementation Strategy

The key to creating truly parallel agents is to use **multiple Task tool calls in a single response**. This is the proven pattern for parallel execution.

### Phase 1: Error Discovery & Distribution

1. **Scan for TypeScript Errors**

   ```bash
   pnpm tsc --noEmit 2>&1 | grep -E "error TS[0-9]+:"
   ```

2. **Scan for ESLint Warnings**

   ```bash
   pnpm eslint . 2>&1 | grep -E "warning|error"
   ```

3. **Parse and Group by File**
   - Extract file paths and error types
   - Group errors by file
   - Identify error categories (TypeScript errors, ESLint warnings)
   - Identify which issues have dependencies on other files and make sure to do those first
   - Each phase should run with the subagents, and when they are done, evaluate and start the next phase
   - Ensure that we fix all root issues first, then their dependent files
   - Create balanced work distribution

4. **Create Agent Work Queues**
   - Distribute files evenly across N agents
   - Balance by error count and complexity
   - Prioritize files with TypeScript errors (higher impact)

### Phase 2: Parallel Agent Execution

**CRITICAL**: Use multiple `Task` tool calls in a single message to create truly parallel agents:

```typescript
// Example parallel task creation:
<invoke name="Task">
<invoke name="Task">
<invoke name="Task">
<invoke name="Task">
<invoke name="Task">
```

Each agent gets:

- Specific list of files to fix
- Error details for each file
- TypeScript best practices guide
- Progress reporting format

### Phase 3: Orchestrated Progress Tracking

1. **Real-time Agent Coordination**
   - Track completion status from each agent
   - Handle agent failures and redistribution
   - Monitor for conflicts or dependencies

2. **Quality Validation**
   - Each agent validates their files pass TypeScript and ESLint
   - Final orchestrator runs full validation
   - Ensure no new errors introduced

## Agent Instructions Template

Each spawned agent receives these specialized instructions:

```markdown
You are a TypeScript/ESLint error fixing specialist. Your specific mission:

### Files Assigned: {file_list}

### Error Categories to Fix:

1. **TypeScript Errors** (PRIORITY 1)
   - Fix all TS errors following patterns from @.claude/guides/typescript-patterns.md
   - NEVER use `@ts-ignore` - fix underlying issues
   - Use `as unknown as Type` for complex type casting
   - ONLY use `any` for complex external infrastructure (Prisma, etc.) and if you do so, include a comment so the linter will ignore just the next line using: // eslint-disable-next-line @typescript-eslint/no-explicit-any

2. **@typescript-eslint/no-explicit-any** (PRIORITY 2)
   - Replace with proper types: `as unknown as Type`
   - Check existing interfaces before creating new ones
   - Create proper interfaces instead of using `any`

3. **@typescript-eslint/no-unused-vars** (PRIORITY 3)
   - Either remove, or prefix with underscore: `_unusedVar`
   - Remove if truly unnecessary
   - Keep if needed for interface compliance

4. **Formatting/Style Issues** (PRIORITY 4)
   - Fix import organization
   - Remove unused imports
   - Fix spacing and formatting

### TypeScript Best Practices (MANDATORY):

- Follow patterns from @.claude/guides/typescript-patterns.md strictly
- NEVER use `@ts-ignore` - fix underlying issues
- Use `as unknown as Type` for complex type casting
- Check for existing factories in src/test-utils/
- Use proper null safety patterns
- Extract nullable values before comparisons

### Validation Requirements:

- Each file must pass: `pnpm tsc --noEmit`
- Each file must pass: `pnpm eslint {file} --max-warnings 0`
- No new TypeScript errors introduced
- Test existing functionality if making significant changes

### Progress Reporting Format:

- "PROGRESS: Agent {id} - {completed}/{total} files - Current: {file}"
- "FIXED: Agent {id} - {file}: {ts_errors} TS errors, {eslint_warnings} ESLint warnings resolved"
- "COMPLETE: Agent {id} - All assigned files clean"
- "ISSUE: Agent {id} - Need help with {file}: {brief_description}"

### Success Criteria:

- ALL assigned files pass TypeScript compilation
- ALL assigned files pass ESLint with 0 warnings
- No TypeScript errors introduced
- Minimal use of `any` (only for complex external infrastructure)
- Code maintains existing functionality
- All fixes follow established patterns
```

## Parallel Execution Pattern

To ensure true parallelism, the orchestrator must:

1. **Create Multiple Task Agents Simultaneously**

   ```typescript
   // In single response, create parallel agents:
   Task(agent1_instructions) +
     Task(agent2_instructions) +
     Task(agent3_instructions) +
     Task(agent4_instructions) +
     Task(agent5_instructions);
   ```

2. **Distribute Work Evenly**

   ```
   Agent 1: scripts/fix-data.ts, scripts/check-data.ts (high TS error files)
   Agent 2: src/lib/services/*.service.ts files
   Agent 3: src/run/process-linkedin/services/*.ts files
   Agent 4: src/test-utils/*.ts and test files
   Agent 5: remaining misc files with errors
   ```

3. **Independent File-Based Work**
   - Each agent works on different files
   - No dependencies between agents
   - Safe to run in true parallel

## Expected Error Types

Based on typical codebases:

1. **TypeScript Errors**:
   - Type mismatches
   - Missing type definitions
   - Interface violations
   - Null/undefined handling

2. **@typescript-eslint/no-explicit-any**:
   - Direct `any` usage
   - Implicit `any` in function parameters
   - `any` in type assertions

3. **@typescript-eslint/no-unused-vars**:
   - Unused imports
   - Unused function parameters
   - Unused variable declarations

4. **Formatting/Style**:
   - Import ordering
   - Spacing issues
   - Missing semicolons

## Error Manifest Format

The error manifest JSON structure:

```json
{
  "summary": {
    "total_files": 45,
    "typescript_errors": 127,
    "eslint_warnings": 89,
    "scan_timestamp": "2024-01-15T10:30:00Z"
  },
  "files": {
    "src/lib/example.ts": {
      "typescript_errors": [
        {
          "line": 15,
          "column": 8,
          "code": "TS2304",
          "message": "Cannot find name 'SomeType'."
        }
      ],
      "eslint_warnings": [
        {
          "line": 23,
          "rule": "@typescript-eslint/no-unused-vars",
          "message": "'unusedVar' is defined but never used."
        }
      ],
      "priority": "high",
      "estimated_difficulty": "medium"
    }
  },
  "agent_assignments": {
    "agent_1": ["src/lib/example.ts", "src/components/Button.tsx"],
    "agent_2": ["src/pages/api/user.ts", "src/utils/helpers.ts"]
  }
}
```

## Progress Dashboard Format

Real-time progress display:

```
🔧 PARALLEL TYPE FIX - Progress Dashboard
═══════════════════════════════════════════════════════════════

📊 OVERALL PROGRESS
Files: ████████████░░░░░░░░░░ 60% (27/45)
TS Errors: ███████████████░░░░░ 75% (95/127)
ESLint: ██████████████████░░░ 85% (76/89)
Time Elapsed: 8m 32s | Est. Remaining: 5m 18s

🤖 AGENT STATUS
Agent 1: ████████████████████ COMPLETE (5/5 files)
Agent 2: ████████████████░░░░ 80% (4/5 files) - Current: api/user.ts
Agent 3: ████████████░░░░░░░░ 60% (3/5 files) - Current: lib/utils.ts
Agent 4: ████████░░░░░░░░░░░░ 40% (2/5 files) - Current: hooks/useDrafts.ts
Agent 5: ████░░░░░░░░░░░░░░░░ 20% (1/5 files) - Current: stores/notification.ts
Agent 6: ░░░░░░░░░░░░░░░░░░░░ 0% (0/5 files) - Starting...

⚠️  ISSUES
Agent 3: Stuck on complex type inference in lib/utils.ts (2m 15s)
Agent 4: Requested guidance on Prisma type casting

🎯 RECENT COMPLETIONS
✅ Agent 1: Fixed 15 TS errors, 8 ESLint warnings in 5 files
✅ Agent 2: Fixed 12 TS errors, 6 ESLint warnings in 4 files
```

## Command Implementation

This command should be implemented as a complex orchestration that:

1. Uses the Task tool to spawn multiple agents
2. Coordinates work distribution
3. Provides real-time progress updates
4. Handles agent failures gracefully
5. Validates final results
6. Generates comprehensive reports

## Success Metrics

- **Error Reduction**: Target 100% TypeScript errors fixed
- **Warning Reduction**: Target 95%+ ESLint warnings fixed
- **No New Errors**: Zero new TypeScript errors introduced
- **Completion Time**: <20 minutes with 5 agents
- **Type Safety**: Minimal `any` usage (only for complex external APIs)
- **Code Quality**: All files pass full validation

## Validation & Reporting

### Final Validation Sequence

```bash
1. pnpm tsc --noEmit              # Must pass with 0 errors
2. pnpm eslint . --max-warnings 0  # Must pass with 0 warnings
3. pnpm test --run                 # Must pass all tests
4. pnpm build                      # Must build successfully
```

### Success Report Format

```
🔧 PARALLEL TYPE FIX - Completion Report
═══════════════════════════════════════════════════════════

📊 RESULTS SUMMARY
Initial TypeScript Errors: 127
Final TypeScript Errors: 0 (-127, 100% reduction)
Initial ESLint Warnings: 278
Final ESLint Warnings: 5 (-273, 98.2% reduction)
Files Processed: 134
Time Taken: 18m 42s

🤖 AGENT PERFORMANCE
Agent 1: 25 files, 32 TS errors, 56 warnings fixed
Agent 2: 28 files, 28 TS errors, 62 warnings fixed
Agent 3: 30 files, 25 TS errors, 48 warnings fixed
Agent 4: 26 files, 22 TS errors, 71 warnings fixed
Agent 5: 25 files, 20 TS errors, 36 warnings fixed

🎯 ERROR CATEGORIES FIXED
TypeScript errors: 127/127 (100%)
@typescript-eslint/no-explicit-any: 198/200 (99%)
@typescript-eslint/no-unused-vars: 75/80 (93.8%)
Formatting/style: All auto-fixed

✅ VALIDATION PASSED
TypeScript: ✅ 0 errors
ESLint: ✅ 5 warnings (acceptable)
Tests: ✅ All passing
Build: ✅ Success
```

## Implementation Notes

### File Prioritization

1. **Critical**: Files with TypeScript compilation errors
2. **High Impact**: Files with many `any` usages
3. **Medium Impact**: Service and lib files with type issues
4. **Low Impact**: Test files and formatting issues

### Error Handling

- If agent gets stuck (>5 min), skip file and report
- If agent fails, redistribute files to other agents
- Always prioritize correctness over speed
- Log all changes for potential rollback

### Post-Completion

1. Run comprehensive validation suite
2. Create commit with detailed changelog
3. Archive logs and progress reports
4. Update TypeScript best practices if new patterns found

This command uses proven parallel execution patterns to efficiently fix all TypeScript and ESLint issues while maintaining code quality and type safety.
