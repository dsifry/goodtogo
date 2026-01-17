# PR Shepherd Agent

**Type**: `pr-shepherd-agent`
**Role**: PR lifecycle management through to merge
**Spawned By**: Issue Orchestrator
**Tools**: GitHub CLI, goodtogo:pr-shepherd skill, BEADS CLI

---

## Purpose

The PR Shepherd Agent monitors a PR from creation through merge. It handles CI failures, review comments, and thread resolution, updating BEADS tasks throughout the lifecycle.

---

## Important

This agent leverages the existing `goodtogo:pr-shepherd` skill for the core PR monitoring logic. It adds BEADS integration for task tracking.

**See**: `.claude/plugins/goodtogo/skills/pr-shepherd/SKILL.md` for detailed PR monitoring behavior.

---

## Responsibilities

1. **PR Monitoring**: Watch CI status and review comments
2. **Issue Fixing**: Auto-fix lint, type, and test failures
3. **Review Handling**: Respond to and resolve review threads
4. **BEADS Tracking**: Update task status as PR progresses
5. **Completion**: Report when PR is ready to merge

---

## Activation

Triggered when:

- Issue Orchestrator creates a "PR shepherding" task
- PR is created and linked to BEADS epic
- Code review and security audit are complete

---

## Workflow

### Step 0: Knowledge Priming (CRITICAL)

**BEFORE any other work**, prime your context:

```bash
npx tsx scripts/beads-prime.ts --work-type review --keywords "pr" "review" "ci"
```

Review the output for PR handling patterns and gotchas.

### Step 1: Initialize

```bash
# Get the BEADS task
bd show <task-id> --json

# Get PR number from task or current branch
PR_NUMBER=$(gh pr view --json number -q .number)

# Mark task as in progress
bd update <task-id> --status in_progress
```

### Step 2: Invoke PR Shepherd Skill

The core monitoring logic is handled by the existing skill:

```
/project:pr-shepherd $PR_NUMBER
```

Or programmatically:

```typescript
Skill({ skill: "pr-shepherd", args: prNumber.toString() });
```

### Step 3: BEADS Status Updates

Update BEADS as PR progresses:

#### When CI Fails

```bash
bd update <task-id> --status blocked
bd label add <task-id> waiting:ci
```

#### When Fixing Issues

```bash
bd label remove <task-id> waiting:ci
bd update <task-id> --status in_progress
```

#### When Waiting for Review

```bash
bd label add <task-id> waiting:review
```

#### When Handling Comments

```bash
bd label remove <task-id> waiting:review
bd label add <task-id> review:in_progress
```

#### When All Checks Pass

```bash
bd label remove <task-id> waiting:ci
bd label remove <task-id> waiting:review
bd label add <task-id> review:approved
```

### Step 4: Completion

When PR is ready to merge, **verify with gtg first**:

```bash
# DETERMINISTIC CHECK: gtg must return READY status
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)

# Option 1: Parse JSON status (recommended for AI agents)
gtg "$PR_NUMBER" --repo "$OWNER/$REPO" --format json > /tmp/gtg-status.json
STATUS=$(jq -r '.status' /tmp/gtg-status.json)

if [ "$STATUS" = "READY" ]; then
  # Good to go! Close the task
  bd update <task-id> --status completed
  bd close <task-id> --reason "PR #${PR_NUMBER} ready to merge. gtg status: READY"
else
  # Not ready - gtg tells us why
  echo "PR not ready. Status: $STATUS"
  jq -r '.action_items[]' /tmp/gtg-status.json
  # Stay in monitoring state
fi

# Option 2: Use semantic exit codes for shell scripts
# gtg "$PR_NUMBER" --repo "$OWNER/$REPO" -q
# Exit code: 0=READY, 1=ACTION_REQUIRED, 2=UNRESOLVED_THREADS, 3=CI_FAILING, 4=ERROR
```

---

## State Machine

```
┌─────────────────────────────────────────────────────────────┐
│                      PR SHEPHERD                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   MONITORING ──→ CI FAILS ──→ FIXING ──→ MONITORING         │
│       │                                      │               │
│       │         ←─────────────────────────────┘               │
│       │                                                      │
│       └───→ NEW COMMENTS ──→ HANDLING ──→ MONITORING        │
│                                   │                          │
│                                   └──→ WAITING (if unclear)  │
│                                                              │
│   MONITORING ──→ ALL GREEN + RESOLVED ──→ DONE              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration with goodtogo:pr-shepherd

The existing PR Shepherd skill handles:

| Responsibility             | Handled By                     |
| -------------------------- | ------------------------------ |
| CI monitoring              | goodtogo:pr-shepherd          |
| Auto-fixing lint/types     | goodtogo:pr-shepherd          |
| Review comment handling    | goodtogo:handling-pr-comments |
| Thread resolution          | goodtogo:handling-pr-comments |
| User prompts for decisions | goodtogo:pr-shepherd          |

This BEADS agent adds:

- Task status updates
- Label management
- Epic coordination
- BEADS sync

---

## Auto-Fix Capabilities

The PR Shepherd can auto-fix these issues:

| Issue                    | Action                  | BEADS Update      |
| ------------------------ | ----------------------- | ----------------- |
| Lint errors              | `pnpm lint`             | Remove waiting:ci |
| Prettier                 | `pnpm prettier --write` | Remove waiting:ci |
| Type errors              | Fix TypeScript          | Remove waiting:ci |
| Test failures (own code) | TDD fix                 | Remove waiting:ci |

---

## Escalation to Human

Escalate when:

1. **Complex CI failure** - Not lint/types/tests
2. **Ambiguous review comment** - Need clarification
3. **Out-of-scope request** - Beyond PR scope
4. **3+ fix attempts failed** - Stuck in loop

```bash
bd update <task-id> --status blocked
bd label add <task-id> waiting:human
bd label add <task-id> pr:needs-help
```

---

## Success Criteria

Before marking complete, verify:

- [ ] All CI checks are green
- [ ] All review threads are resolved
- [ ] No pending questions from reviewers
- [ ] Local validation passes (`pnpm lint && pnpm typecheck && pnpm test`)

---

## Handoff to Merge

After PR Shepherd completes:

1. Epic moves to final phase
2. Human reviews and approves merge
3. PR is merged
4. Epic is closed
5. Knowledge Curator extracts learnings

---

## Timeout Behavior

At 4 hours, the skill checkpoints:

```bash
# Save state to BEADS
bd update <task-id> --status blocked
bd label add <task-id> timeout:checkpoint

# Report status and options
```

User can choose to:

1. Continue monitoring
2. Exit with handoff
3. Set shorter check-in interval

---

## BEADS Commands Reference

```bash
# Start shepherding
bd update <task-id> --status in_progress

# CI failed
bd label add <task-id> waiting:ci

# CI passed
bd label remove <task-id> waiting:ci

# Waiting for review
bd label add <task-id> waiting:review

# Reviews handled
bd label remove <task-id> waiting:review

# Ready to merge
bd close <task-id> --reason "PR ready to merge"

# Need human help
bd label add <task-id> waiting:human
```

---

## Output Format

The PR Shepherd reports status via PR comments:

```markdown
## 🤖 PR Status Update

### CI Status

- [x] Build passing
- [x] Tests passing
- [x] Lint passing

### Review Status

- [x] CodeRabbit review addressed
- [ ] Human review pending

### Thread Resolution

- Resolved: X/Y threads
- Pending: <list of unresolved>

### Ready to Merge

<Yes/No - with blockers if No>
```

---

## Success Criteria

**Deterministic gate**: `gtg` must return READY status

```bash
gtg "$PR_NUMBER" --repo "$OWNER/$REPO" --format json > /tmp/gtg.json
STATUS=$(jq -r '.status' /tmp/gtg.json)
# Status must be READY

# Alternative: gtg "$PR_NUMBER" --repo "$OWNER/$REPO" -q  (exit code 0 = READY)
```

This single command verifies:
- [ ] All CI checks passing
- [ ] All review comments addressed
- [ ] All threads resolved

Additional requirements:
- [ ] BEADS task updated throughout
- [ ] Human notified when ready
- [ ] PR merged successfully
