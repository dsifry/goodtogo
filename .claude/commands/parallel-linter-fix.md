# Parallel Linter Fix Command

## Overview

This command systematically finds all ESLint warnings across the codebase, distributes the work across parallel subagents, and provides real-time progress tracking. Each agent fixes linter issues in parallel since they are independent file-based changes.

## Usage

```
/project:parallel-linter-fix [options]
```

### Options

- `--agents=N` - Number of parallel agents (default: 5, max: 8)
- `--focus=any|unused|formatting|all` - Type of warnings to focus on (default: all)
- `--dry-run` - Show what would be done without making changes
- `--verbose` - Show detailed progress and warning information

### Examples

```
/project:parallel-linter-fix
/project:parallel-linter-fix --agents=3 --focus=any
/project:parallel-linter-fix --dry-run --verbose
```

## Implementation Strategy

The key to creating truly parallel agents is to use **multiple Task tool calls in a single response**. This is the proven pattern for parallel execution.

### Phase 1: Warning Discovery & Distribution

1. **Scan for ESLint Warnings**

   ```bash
   pnpm eslint . 2>&1 | grep -E "warning|error"
   ```

2. **Parse and Group by File**
   - Extract file paths and warning types
   - Group warnings by file
   - Identify warning categories (any, unused vars, formatting, etc.)
   - Create balanced work distribution

3. **Create Agent Work Queues**
   - Distribute files evenly across N agents
   - Balance by warning count and complexity
   - Prioritize files with `@typescript-eslint/no-explicit-any` warnings

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
- Warning details for each file
- TypeScript best practices guide
- Progress reporting format

### Phase 3: Orchestrated Progress Tracking

1. **Real-time Agent Coordination**
   - Track completion status from each agent
   - Handle agent failures and redistribution
   - Monitor for conflicts or dependencies

2. **Quality Validation**
   - Each agent validates their files pass ESLint
   - Final orchestrator runs full lint check
   - Ensure no new errors introduced

## Agent Instructions Template

Each spawned agent receives these specialized instructions:

```markdown
You are an ESLint warning fixing specialist. Your specific mission:

### Files Assigned: {file_list}

### Warning Categories to Fix:

1. **@typescript-eslint/no-explicit-any** (PRIORITY 1)
   - Replace with proper types: `as unknown as Type`
   - Check existing interfaces before creating new ones
   - ONLY use `any` for complex external infrastructure (Prisma, etc.) and if you do so, include a comment so the linter will ignore just the next line

2. **@typescript-eslint/no-unused-vars** (PRIORITY 2)
   - Either remove, or prefix with underscore: `_unusedVar`
   - Remove if truly unnecessary
   - Keep if needed for interface compliance

3. **Formatting/Style Issues** (PRIORITY 3)
   - Fix import organization
   - Remove unused imports
   - Fix spacing and formatting

### TypeScript Best Practices (MANDATORY):

- Follow patterns from @.claude/guides/typescript-patterns.md
- NEVER use `@ts-ignore` - fix underlying issues
- Use `as unknown as Type` for complex type casting
- Check for existing factories in src/test-utils/
- Use proper null safety patterns

### Validation Requirements:

- Each file must pass: `pnpm eslint {file} --max-warnings 0`
- No new TypeScript errors introduced
- Test existing functionality if making significant changes

### Progress Reporting Format:

- "PROGRESS: Agent {id} - {completed}/{total} files - Current: {file}"
- "FIXED: Agent {id} - {file}: {warning_count} warnings resolved"
- "COMPLETE: Agent {id} - All assigned files clean"
- "ISSUE: Agent {id} - Need help with {file}: {brief_description}"

### Success Criteria:

- ALL assigned files pass ESLint with 0 warnings
- No TypeScript errors introduced
- Minimal use of `any` (only for complex external infrastructure)
- Code maintains existing functionality
```

## Parallel Execution Pattern

To ensure true parallelism, the orchestrator must:

1. **Create Multiple Task Agents Simultaneously**

   ```typescript
   // In single response, create 5 parallel agents:
   Task(agent1_instructions) +
     Task(agent2_instructions) +
     Task(agent3_instructions) +
     Task(agent4_instructions) +
     Task(agent5_instructions);
   ```

2. **Distribute Work Evenly**

   ```
   Agent 1: scripts/fix-data.ts, scripts/collect-linkedin-data.ts
   Agent 2: src/lib/services/sales-intelligence.service.ts
   Agent 3: src/run/process-linkedin/services/location-analysis.service.ts
   Agent 4: src/test-utils/*.ts files
   Agent 5: remaining misc files
   ```

3. **Independent File-Based Work**
   - Each agent works on different files
   - No dependencies between agents
   - Safe to run in true parallel

## Expected Warning Categories

Based on current scan (506 warnings):

1. **@typescript-eslint/no-explicit-any**: ~200 warnings
   - Mostly in scripts/ directory
   - Some in services and test utilities
   - High priority for type safety

2. **@typescript-eslint/no-unused-vars**: ~150 warnings
   - Import statements
   - Function parameters
   - Variable declarations

3. **Import/Export Issues**: ~100 warnings
   - Unused imports
   - Import organization
   - Missing exports

4. **Formatting/Style**: ~56 warnings
   - Spacing, semicolons, etc.
   - Usually auto-fixable

## Success Metrics

- **Warning Reduction**: Target 95%+ (506 → <25)
- **No New Errors**: Zero TypeScript errors introduced
- **Completion Time**: <15 minutes with 5 agents
- **Type Safety**: Minimal `any` usage (only for complex external APIs)
- **Code Quality**: All files pass `pnpm eslint --max-warnings 0`

## Validation & Reporting

### Final Validation Sequence

```bash
1. pnpm eslint . --max-warnings 0    # Must pass
2. pnpm typecheck                    # Must pass
3. pnpm test --run                   # Must pass
4. pnpm build                        # Must pass
```

### Success Report Format

```
🧹 PARALLEL LINTER FIX - Completion Report
═══════════════════════════════════════════════════════════

📊 RESULTS SUMMARY
Initial Warnings: 506
Final Warnings: 12 (-494, 97.6% reduction)
Files Processed: 89
Time Taken: 12m 34s

🤖 AGENT PERFORMANCE
Agent 1: 18 files, 145 warnings fixed
Agent 2: 16 files, 98 warnings fixed
Agent 3: 20 files, 112 warnings fixed
Agent 4: 15 files, 89 warnings fixed
Agent 5: 20 files, 50 warnings fixed

🎯 WARNING CATEGORIES FIXED
@typescript-eslint/no-explicit-any: 198/200 (99%)
@typescript-eslint/no-unused-vars: 148/150 (98.7%)
Import/export issues: 95/100 (95%)
Formatting/style: 53/56 (94.6%)

✅ VALIDATION PASSED
ESLint: ✅ 0 warnings
TypeScript: ✅ 0 errors
Tests: ✅ All passing
Build: ✅ Success
```

## Implementation Notes

### File Prioritization

1. **High Impact**: Files with many `any` usages (scripts/fix-data.ts)
2. **Medium Impact**: Service files with type issues
3. **Low Impact**: Test utilities and formatting issues

### Error Handling

- If agent gets stuck (>5 min), skip file and report
- If agent fails, redistribute files to other agents
- Always prioritize code safety over speed
- Log all changes for rollback if needed

### Post-Completion

1. Run comprehensive validation suite
2. Create commit with detailed changelog
3. Archive logs and progress reports
4. Update TypeScript best practices if new patterns found

This command focuses specifically on ESLint warnings while maintaining the type safety we just achieved in the TypeScript cleanup.
