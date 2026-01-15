# pr-shepherd

Use when a PR has been created and needs to be monitored through to merge - handles CI failures, review comments, and thread resolution automatically until all checks pass and all threads are resolved.

**IMPORTANT**: This skill is designed for the **agent working in a worktree**, NOT the orchestrator. The agent handles its own PR monitoring so the orchestrator remains free for other work.

## When to Activate

Activate this skill when ANY of these conditions are true:

- Agent just created a PR with `gh pr create`
- User asks to "shepherd", "monitor", or "see through" a PR
- User invokes `/project:pr-shepherd <pr-number>`
- User asks to "watch this PR" or "handle this PR until it's merged"
- Orchestrator spawned you with instructions to shepherd a PR
- **Automatic**: `bin/create-pr-with-shepherd.sh` was used (outputs shepherd instructions)

### Automatic Activation via Wrapper Script

When `bin/create-pr-with-shepherd.sh` creates a PR, it outputs shepherd instructions:

```text
==========================================
  PR Shepherd Active for PR #123
==========================================

The pr-shepherd skill will:
  - Monitor CI/CD status
  - Auto-fix lint, type, and test issues
  - Handle review comments
  - Resolve threads after addressing feedback
  - Report when PR is ready to merge

To manually invoke shepherd later:
  /project:pr-shepherd 123
```

When you see this output, **immediately invoke the pr-shepherd skill** with the PR number shown.

## Announce at Start

"I'm using the pr-shepherd skill to monitor this PR through to merge. I'll watch CI/CD, handle review comments, and fix issues as they arise."

## For Orchestrators: Spawning Agents with PR Shepherding

When spawning an agent to work in a worktree, include PR shepherding in the task prompt:

```text
Work in worktree at /path/to/worktree on branch feature/xyz.

Task: [describe the implementation task]

After creating the PR:
1. Use the pr-shepherd skill to monitor it through to merge
2. Handle CI failures and review comments autonomously
3. Only escalate to orchestrator for complex issues requiring user input
4. Report back when PR is ready to merge or if blocked

Run in background so I can continue other work.
```

**Key principle**: The agent owns its PR lifecycle. The orchestrator spawns and forgets, checking back via `AgentOutputTool` when needed.

## State Machine

The agent operates in one of these states:

```text
MONITORING → FIXING → MONITORING → WAITING_FOR_USER → FIXING → MONITORING → DONE
```

| State              | What Happens                                | Exit When                                      |
| ------------------ | ------------------------------------------- | ---------------------------------------------- |
| `MONITORING`       | Poll CI and reviews every 60s in background | CI fails, new comments, all done, or need help |
| `FIXING`           | Fix issues using TDD, run local validation  | Local validation passes OR need user guidance  |
| `HANDLING_REVIEWS` | Invoke `handling-pr-comments` skill         | Comments handled OR need user input            |
| `WAITING_FOR_USER` | Present options, wait for user decision     | User responds                                  |
| `DONE`             | All CI green + all threads resolved         | Exit successfully                              |

## Phase 1: Initialize

```bash
# Get PR info
PR_NUMBER=$(gh pr view --json number -q .number 2>/dev/null)
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)

# If no PR on current branch, check if number was provided
if [ -z "$PR_NUMBER" ]; then
  echo "No PR found for current branch. Provide PR number."
  exit 1
fi

echo "Shepherding PR #$PR_NUMBER"
```

## Phase 2: Monitoring Loop (Background)

Run `gtg check` every 60 seconds to get deterministic PR status:

### Using gtg for PR Status

```bash
# Run gtg check and capture exit code
gtg check "$OWNER/$REPO" "$PR_NUMBER" --json > /tmp/gtg-status.json
GTG_EXIT=$?

# Parse the JSON for details
STATUS=$(jq -r '.status' /tmp/gtg-status.json)
CI_STATE=$(jq -r '.ci_status.state' /tmp/gtg-status.json)
UNRESOLVED=$(jq -r '.threads.unresolved' /tmp/gtg-status.json)
ACTIONABLE_COUNT=$(jq -r '.actionable_comments | length' /tmp/gtg-status.json)
```

### gtg Exit Codes → State Transitions

| Exit Code | Status | Action |
|-----------|--------|--------|
| 0 | `READY` | → DONE (all clear!) |
| 1 | `ACTION_REQUIRED` | → HANDLING_REVIEWS (actionable comments) |
| 2 | `UNRESOLVED` | → HANDLING_REVIEWS (threads need resolution) |
| 3 | `CI_FAILING` | → FIXING (CI failures) |
| 4 | `ERROR` | → WAITING_FOR_USER (API error) |

### Evaluate State Transitions

```bash
case $GTG_EXIT in
  0)  # READY - all clear
      echo "✅ PR is good to go!"
      # → DONE
      ;;
  1)  # ACTION_REQUIRED - actionable comments exist
      echo "📝 Actionable comments need attention"
      jq -r '.action_items[]' /tmp/gtg-status.json
      # → HANDLING_REVIEWS
      ;;
  2)  # UNRESOLVED - threads need resolution
      echo "💬 Unresolved threads: $UNRESOLVED"
      # → HANDLING_REVIEWS
      ;;
  3)  # CI_FAILING - CI checks failing
      echo "❌ CI failing:"
      jq -r '.ci_status.checks[] | select(.status == "failure") | "  - \(.name)"' /tmp/gtg-status.json
      # → FIXING (if simple) or WAITING_FOR_USER (if complex)
      ;;
  4)  # ERROR - couldn't fetch PR data
      echo "⚠️ Error fetching PR data"
      # → WAITING_FOR_USER
      ;;
esac
```

## Phase 3: Fixing Issues

### Simple Issues (Auto-fix)

These can be fixed without user approval:

- Lint failures → run `pnpm lint`
- Prettier failures → run `pnpm prettier --write`
- Type errors → fix the types
- Test failures in code YOU wrote → fix using TDD

### Complex Issues (Need Approval)

These require user input BEFORE fixing:

- Test failures in code you didn't write
- Infrastructure/config failures
- Ambiguous errors
- Anything you're uncertain about

### FIXING State Rules

1. **Use TDD** - Invoke `superpowers:test-driven-development` for code changes
2. **Stay until green** - Don't leave FIXING until `pnpm lint && pnpm typecheck && pnpm test --run` pass
3. **Only push when verified** - Never push code that fails local validation
4. **Return to MONITORING after push** - Let CI run, continue monitoring

```bash
# After fixing, always validate locally
pnpm lint && pnpm typecheck && pnpm test --run

# Only push if all pass
git add -A && git commit -m "fix: <description>" && git push
```

## Phase 4: Handling Reviews

When new review comments are detected:

1. Invoke the `goodtogo:handling-pr-comments` skill
2. That skill handles categorization, fixes, responses, and thread resolution
3. **⚠️ CRITICAL: The handling-pr-comments skill includes an iteration loop**
4. **ALL threads must be resolved** before returning to MONITORING
5. If a thread cannot be resolved (needs clarification from reviewer), query the comment author asking for follow-up
6. Return to MONITORING only when:
   - All threads are resolved, AND
   - Post-push verification confirms NO new comments appeared

### Iteration Enforcement

**⚠️ THE #1 FAILURE MODE**: Returning to MONITORING after one pass without checking for new comments.

The `handling-pr-comments` skill's Phase 7 (Post-Push Iteration Check) MUST complete successfully before exiting HANDLING_REVIEWS state. The skill will iterate automatically:

```text
HANDLING_REVIEWS:
  → handling-pr-comments skill (Phases 1-7)
  → IF Phase 7 finds new comments: skill re-runs Phases 1-7
  → IF Phase 7 confirms no new comments: exit to MONITORING
```

**DO NOT** manually override or skip Phase 7. If you find yourself tempted to skip iteration, you're about to make the #1 mistake.

### Out-of-Scope Comments

Reviewers may leave comments on code outside the PR diff. The `handling-pr-comments` skill handles these, but key points:

- **Treat out-of-scope as IN SCOPE by default** - respect reviewer feedback
- Use **ultrathink** to evaluate if fixes are quick (< 30 min, < 3 files)
- If simple: fix immediately and note it was outside original scope
- If complex: create a GitHub issue and link it in the thread response
- **Always respond and resolve** - never leave out-of-scope threads hanging

## Phase 5: Waiting for User

When user input is needed, ALWAYS:

1. **Present the situation clearly**
2. **Offer 2-4 options with pros/cons**
3. **State your recommendation**
4. **Allow user to choose OR provide their own approach**

### Template

```text
[Describe what happened]

**Options:**

1. **[Option name]** (Recommended)
   - [What it involves]
   - Pros: [benefits]
   - Cons: [drawbacks]

2. **[Option name]**
   - [What it involves]
   - Pros: [benefits]
   - Cons: [drawbacks]

3. **[Option name]**
   - [What it involves]
   - Pros: [benefits]
   - Cons: [drawbacks]

Which approach would you like? (Or describe a different approach)
```

### After User Responds

- If user picks a numbered option → proceed with that approach → FIXING
- If user describes alternative → proceed with their approach → FIXING

## Phase 6: Soft Timeout (4 Hours)

At 4 hours elapsed, pause and checkpoint:

```text
**PR Shepherd Checkpoint** (4 hours elapsed)

Current status:
- CI: [status]
- Threads: [X] resolved, [Y] unresolved
- Commits: [N] fix commits pushed

**Options:**

1. **Keep monitoring** (Recommended)
   - Continue for another 4 hours
   - Pros: PR may get reviewed soon
   - Cons: Ties up agent resources

2. **Exit with handoff**
   - Save status report, exit cleanly
   - Pros: Frees resources
   - Cons: Must manually re-invoke later

3. **Set shorter check-in**
   - Check back in 1 hour instead of 4
   - Pros: More frequent checkpoints
   - Cons: More interruptions

What would you like to do? (Or describe a different approach)
```

## Exit Conditions

### Success (DONE)

Exit successfully when ALL are true:

- ✅ All CI checks passing
- ✅ All review threads resolved
- ✅ No pending questions

Report:

```text
**PR #[number] Ready to Merge** ✅

- CI: All checks passing
- Reviews: All threads resolved
- Commits: [N] total ([M] fix commits)

The PR is ready for final approval and merge.
```

### Post-Completion RAM Cleanup

After the PR is merged and knowledge extraction tasks are created, invoke automatic RAM cleanup to free resources:

```text
/project:auto-ram-cleanup
```

**Why**: Development processes (test runners, build watchers, language servers) accumulate during PR work. Cleaning up after merge frees memory for the next task.

**What stays running**:

- Docker containers (needed for database/services)
- Essential IDE processes

**What gets cleaned**:

- Orphaned test runners (vitest, jest)
- Build watchers no longer needed
- Duplicate language server instances
- Other development tool cruft

## Phase 7: Post-Merge Knowledge Extraction

**IMPORTANT**: After a PR is merged into main, create a blocking BEADS task for knowledge extraction. This ensures CodeRabbit learnings are captured before the epic can be closed.

### When PR is Merged

After detecting that the PR has been merged (or after user merges it):

```bash
# Check if PR was merged
MERGED=$(gh pr view $PR_NUMBER --json merged -q .merged)

if [ "$MERGED" = "true" ]; then
  # Create a BEADS task for knowledge curation
  bd create \
    --title="Curate learnings from PR #$PR_NUMBER" \
    --type=task \
    --priority=2 \
    --label="knowledge-extraction"

  # Note the new task ID from output
  CURATION_TASK_ID="<id from bd create output>"

  # If there's an associated epic, add this task as a blocker
  # (The epic can't close until learnings are extracted)
  if [ -n "$EPIC_ID" ]; then
    bd dep add "$EPIC_ID" "$CURATION_TASK_ID"
  fi
fi
```

### Report to User

When creating the curation task:

````text
**PR #[number] Merged Successfully** ✅

Created blocking task: [CURATION_TASK_ID]
- Title: "Curate learnings from PR #[number]"
- Status: pending
- Blocker for: [epic if applicable]

To extract learnings, invoke:
```
/project:curate-pr-learnings [number]
```

The command will:
1. Fetch PR comments (deterministic script)
2. AI analyzes and extracts learnings (your job)
3. Store validated learnings (deterministic script)

Then close the task:
```bash
bd close [CURATION_TASK_ID]
```
````

### Why This Matters

1. **Security**: Webhook-triggered code execution is an attack surface. CLI/agent invocation is safer.
2. **Blocking Task**: The epic can't close until learnings are extracted, ensuring knowledge capture.
3. **Agent Autonomy**: An agent can pick up the curation task from `bd ready` and process it.
4. **Human Oversight**: Human can also run curation manually via the CLI script.

### For Epic Completions: Extract Conversation Learnings

When this PR completes an **epic** (closes the last blocking task), you MUST also extract learnings from conversation history. Feature work often contains the richest architectural discussions.

**Detect epic completion:**

> **Note**: This pattern assumes single-epic workflows. If multiple epics are in-progress,
> `.[0]` selects the first one, which may not be the epic related to this PR.
> For multi-epic projects, correlate the PR's task to its blocking epic manually.

```bash
# Check if this PR closes an epic (assumes single in-progress epic)
EPIC_ID=$(bd list --status=in_progress --type=epic --json | jq -r '.[0].id // empty')

if [ -n "$EPIC_ID" ]; then
  # Check if epic will have no more blockers after this PR closes
  REMAINING_BLOCKERS=$(bd show "$EPIC_ID" --json | jq '[.blockedBy[] | select(.status != "closed")] | length')

  if [ "$REMAINING_BLOCKERS" -eq 0 ]; then
    echo "This PR completes epic $EPIC_ID - conversation extraction required"
  fi
fi
```

**If epic is completing:**

1. Create a BEADS task for conversation extraction:

   ```bash
   CONV_TASK_ID=$(bd create \
     --title="Extract learnings from epic $EPIC_ID conversations" \
     --type=task \
     --priority=2 \
     --label="knowledge-extraction")

   # Block epic until extraction is done
   bd dep add "$EPIC_ID" "$CONV_TASK_ID"
   ```

2. Report the task to user:

   ```text
   **Epic Completion Detected** 🎯

   This PR completes epic $EPIC_ID. Created conversation extraction task:
   - Task: $CONV_TASK_ID
   - Title: "Extract learnings from epic conversations"
   - Status: Blocking epic close

   Before closing the epic, run:
   /project:extract-learnings --historical --recent 10

   Then close the extraction task:
   bd close $CONV_TASK_ID
   bd close $EPIC_ID
   ```

**Why extract from conversations?**

- **Strategic insights**: Architectural decisions, trade-offs discussed
- **Debugging discoveries**: Root causes found after hours of investigation
- **Non-obvious behaviors**: "It turns out that..." moments
- **Integration quirks**: API behaviors that caused issues

These learnings are often NOT in CodeRabbit comments - they're in the back-and-forth conversation.

### Timeout with Handoff

If user chooses to exit at checkpoint:

```text
**PR #[number] Shepherd Handoff**

Status at exit:
- CI: [status]
- Threads: [X] resolved, [Y] unresolved
- Last activity: [timestamp]

To resume: `/project:pr-shepherd [number]`
```

## Skills Invoked

| Situation           | Skill                                 |
| ------------------- | ------------------------------------- |
| New review comments | `goodtogo:handling-pr-comments`      |
| Code changes needed | `superpowers:test-driven-development` |
| Complex debugging   | `superpowers:systematic-debugging`    |

## Mandatory Pre-Completion Check

**⚠️ BLOCKING: You MUST run `gtg check` and verify exit code 0 before declaring ANY PR ready:**

```bash
gtg check "$OWNER/$REPO" "$PR_NUMBER"
echo "Exit code: $?"
```

### gtg Exit Code Meanings

| Exit | Status | Meaning |
|------|--------|---------|
| 0 | READY | ✅ All clear - good to go! |
| 1 | ACTION_REQUIRED | ❌ Actionable comments need fixes |
| 2 | UNRESOLVED | ❌ Unresolved review threads |
| 3 | CI_FAILING | ❌ CI checks failing |
| 4 | ERROR | ❌ Error fetching data |

**If exit code is NOT 0, you are NOT done.** Address each issue:

For EACH top-level comment (where `in_reply_to_id` is null) without a reply:

1. If actionable → Fix it and reply confirming the fix
2. If out-of-scope → Reply explaining deferral (create issue if needed)
3. If disagree → Reply with reasoning
4. **NEVER ignore silently**

A PR is NOT ready until every top-level comment has been addressed with a reply.

## Verification Checklist

Before exiting DONE state:

- [ ] All CI checks are green
- [ ] All review threads are resolved
- [ ] No pending user questions
- [ ] Final status reported to user

After PR is merged (Phase 7):

- [ ] Created BEADS task for knowledge curation
- [ ] Added task as blocker to epic (if applicable)
- [ ] Reported curation task ID to user

After all post-merge tasks complete:

- [ ] Ran `/project:auto-ram-cleanup` to free development resources
- [ ] Confirmed Docker containers still running (if needed)

## Common Mistakes

### 🚨 #1 MISTAKE: Returning to MONITORING without checking for NEW comments

- After pushing a fix and responding to threads, you MUST run Phase 7
- Automated reviewers (CodeRabbit, Cursor) analyze every commit
- NEW comments often appear within 1-2 minutes of your push
- If you skip Phase 7, you'll miss the new comments and declare complete prematurely

**Pushing without local validation**

- NEVER push code that hasn't passed `pnpm lint && pnpm typecheck && pnpm test --run`

**Auto-fixing complex issues**

- If uncertain, ASK. Always go through WAITING_FOR_USER for complex issues.

**Forgetting to invoke handling-pr-comments**

- When new comments arrive, delegate to that skill. Don't handle comments inline.

**Not presenting options to user**

- Always give 2-4 options with pros/cons. Never just ask "what should I do?"

**Leaving FIXING state early**

- Stay in FIXING until local validation passes. Don't assume a fix worked.

**Skipping the handling-pr-comments iteration loop**

- The skill has Phases 1-7 with an explicit iteration loop
- Phase 7 checks for new comments after your fix push
- If Phase 7 finds new comments, the skill loops back to Phase 1
- DO NOT exit early - let the skill complete its full iteration
