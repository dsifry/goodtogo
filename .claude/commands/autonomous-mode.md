# /project:autonomous-mode

> ⚠️ **Note**: `/project:autonomous-mode` is a Claude slash command.  
> Type it directly into the chat interface. Attempting to run it in Bash or a
> shell will fail with "no such file or directory".

Enable Claude Code to work autonomously on approved tasks while you're away, with comprehensive safety guardrails.

## Usage

```
/project:autonomous-mode <duration-hours>
```

## Overview

This command allows Claude Code to work independently on pre-approved tasks while maintaining safety through:

- Explicit plan approval before execution
- Non-destructive operations only
- Comprehensive logging and reporting
- Automatic fallback strategies for risky operations

## Workflow

### 1. Pre-Autonomous Checklist

```bash
# Verify clean git state
git status --porcelain
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️ WARNING: Uncommitted changes detected. Please commit or stash before autonomous mode."
fi

# Create safety checkpoint
git checkout -b autonomous-backup-$(date +%Y%m%d-%H%M%S)
git add -A && git commit -m "Safety checkpoint before autonomous mode"

# Check current todos
/todo-read
```

### 2. Plan Generation Phase

Claude will use **ultrathink** mode to:

1. Analyze current task state and todos
2. Generate detailed execution plan
3. Identify potential risks and mitigations
4. Create fallback strategies

**Plan Template**:

```markdown
## Autonomous Execution Plan

**Duration**: <X> hours
**Start Time**: <timestamp>
**Expected End**: <timestamp>

### Tasks to Complete

1. [ ] Task 1 - <description>
   - Files to modify: <list>
   - Tests to run: <list>
   - Risk level: Low/Medium
2. [ ] Task 2 - <description>
   - Files to modify: <list>
   - Dependencies: Task 1
   - Risk level: Low/Medium

### Safety Constraints

- ✅ No database deletions or destructive migrations
- ✅ No uncommitted file deletions
- ✅ No force pushes or repository operations
- ✅ Create new files instead of overwriting when uncertain
- ✅ All changes must pass tests and build
- ✅ Stop if error rate exceeds 3 consecutive failures

### Fallback Strategies

- If file deletion needed → Rename to .backup-<timestamp>
- If migration needed → Create reversible migration only
- If tests fail → Create fix attempt in separate branch
- If build fails → Document issue and continue other tasks

### Post-Execution Questions

- [ ] Review renamed/backup files for deletion
- [ ] Approve any database migrations
- [ ] Review any architectural decisions
```

### 3. Approval Required

```
> **Ready for Autonomous Mode**
>
> I've analyzed the current state and created an execution plan for the next <X> hours.
>
> **Summary**: <brief description of what will be accomplished>
>
> Please review the plan above and confirm with:
> - YES - Proceed with autonomous execution
> - NO - Cancel and return to normal mode
> - MODIFY - Adjust the plan
```

### 4. Autonomous Execution Phase

Once approved, Claude will:

#### Enable Enhanced Permissions

Temporarily add to `.claude/settings.local.json`:

```json
{
  "permissions": {
    "autonomous_mode": true,
    "autonomous_until": "<timestamp>",
    "allow": [
      // Existing permissions plus:
      "Write(*)",
      "Edit(*)",
      "MultiEdit(*)",
      "Task(*)",
      "TodoWrite(*)",
      "Bash(npm test)",
      "Bash(pnpm test --run)",
      "Bash(pnpm build)",
      "Bash(git checkout -b *)",
      "Bash(cp *)", // For backup operations
      "Bash(mv * *.backup-*)" // For safe renames
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force*)",
      "Bash(dropdb *)",
      "Bash(DELETE FROM *)",
      "Write(*.env)",
      "Write(*/migrations/*)"
    ]
  }
}
```

#### Execution Loop

```python
while current_time < end_time:
    # 1. Check todo list
    todos = TodoRead()

    # 2. Select next task
    task = select_next_task(todos)

    # 3. Execute with safety checks
    try:
        execute_task(task)
        mark_completed(task)
    except Exception as e:
        log_error(e)
        if consecutive_errors > 3:
            enter_safe_mode()

    # 4. Validate changes
    run_tests()
    check_build()

    # 5. Create checkpoint
    if significant_progress:
        git_commit_checkpoint()
```

### 5. Safety Mechanisms

#### Non-Destructive File Operations

```bash
# Instead of deleting
mv old-file.ts old-file.ts.backup-20250624-1430

# Instead of overwriting uncertain files
cp original.ts original.ts.autonomous-working
# Work on copy, leave original untouched
```

#### Error Escalation

```markdown
## Autonomous Mode - Issue Encountered

**Time**: <timestamp>
**Task**: <current task>
**Issue**: <description>

**Attempted Solutions**:

1. <attempt 1> - Failed: <reason>
2. <attempt 2> - Failed: <reason>

**Fallback Action**: Skipping to next task, documenting for user review
```

#### Progress Reporting

Every 30 minutes or major milestone:

```markdown
## Autonomous Progress Report - <timestamp>

**Completed**:

- ✅ Task 1: <summary>
- ✅ Task 2: <summary>

**In Progress**:

- 🔄 Task 3: 60% complete

**Blocked/Skipped**:

- ❌ Task 4: Requires user decision on <issue>

**System Health**:

- Tests: Passing ✅
- Build: Success ✅
- Errors: 0
```

### 6. Exit and Handoff

When time expires or all tasks complete:

```markdown
## Autonomous Mode - Completion Report

**Duration**: <actual hours>
**Tasks Completed**: X/Y
**Success Rate**: XX%

### Completed Work

1. ✅ <task summary> - <key changes>
2. ✅ <task summary> - <key changes>

### Requires Your Attention

1. 🔍 Review backup files for deletion:
   - old-file.ts.backup-20250624-1430
   - config.json.backup-20250624-1445

2. 💭 Architecture Decisions:
   - <decision point 1>
   - <decision point 2>

3. ⚠️ Blocked Items:
   - <blocker description>

### Next Steps

1. Review the completion report
2. Address items requiring attention
3. Run `/project:cleanup-autonomous` to clean backup files
```

## Configuration Options

### Duration Limits

- Minimum: 1 hour
- Maximum: 8 hours
- Recommended: 2-4 hours for optimal results

### Risk Levels

```yaml
low_risk:
  - Documentation updates
  - Test additions
  - Formatting fixes
  - Type corrections

medium_risk:
  - New feature implementation
  - Refactoring with tests
  - API endpoint additions
  - UI component creation

high_risk: # Requires explicit approval
  - Database schema changes
  - Authentication modifications
  - Payment processing updates
  - Breaking API changes
```

## Best Practices

1. **Clear Task Definition**: Ensure all todos are well-defined before starting
2. **Test Coverage**: Have good test coverage for autonomous validation
3. **Git State**: Always start with a clean git state
4. **Time Blocks**: Use shorter durations initially (1-2 hours)
5. **Review Habit**: Always review the completion report thoroughly

## Example Usage

```
Human: I need to implement the new contact import feature. I'll be back in 3 hours.

Claude: /project:autonomous-mode 3

[Claude generates plan]
```
