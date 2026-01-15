# Worktree Development Guide

This guide covers git worktree usage patterns for parallel development in the Warmstart codebase.

## Table of Contents

- [When to Use Worktrees](#when-to-use-worktrees)
- [Worktree Setup](#worktree-setup)
- [Workflow Patterns](#workflow-patterns)
- [Multi-Agent Coordination](#multi-agent-coordination)
- [Database Safety](#database-safety)
- [Troubleshooting](#troubleshooting)

## When to Use Worktrees

### Good Use Cases

| Scenario                               | Why Worktrees Help                                            |
| -------------------------------------- | ------------------------------------------------------------- |
| **Multiple PRs in review**             | Work on new features while PRs await review                   |
| **Parallel feature development**       | Multiple agents can work on different features simultaneously |
| **Testing against different branches** | Compare behavior across branches without stashing             |
| **Long-running tasks**                 | Don't block other work while waiting for builds/tests         |
| **Code review reference**              | Keep PR code open while working on something else             |

### When NOT to Use Worktrees

- **Simple, quick tasks** - Overhead isn't worth it for 5-minute fixes
- **Tight integration work** - When changes need to see each other immediately
- **Schema migrations** - Database is shared; coordinate carefully
- **Single-branch workflow** - If you're only working on one thing

## Worktree Setup

### Creating a Worktree

From the **main repository** (not from another worktree):

```bash
# Using worktree scripts (recommended)
pnpm worktree:setup agent-2 feature/new-feature

# Or using git directly
git worktree add ~/Developer/goodtogo-worktrees/agent-2 -b feature/new-feature
```

### Worktree Directory Structure

```text
~/Developer/
├── goodtogo/                      # Main repository
│   └── .claude/
│       └── handoffs/               # Handoff documents
└── goodtogo-worktrees/            # All worktrees live here
    ├── agent-2/
    │   └── .claude/
    │       └── handoffs/
    ├── hotfix/
    └── experiment/
```

### Environment Isolation

When using `pnpm worktree:setup`, each worktree gets:

| Variable           | Main Repo | Worktree Example |
| ------------------ | --------- | ---------------- |
| `PORT`             | 3000      | 3001             |
| `REDIS_KEY_PREFIX` | (none)    | `agent-2:`       |
| `WORKTREE_ID`      | (unset)   | `agent-2`        |

This prevents port conflicts and Redis key collisions.

## Workflow Patterns

### Starting Work in a New Worktree

1. Create the worktree from main repo:

   ```bash
   /project:worktree-create agent-2 feature/my-feature
   ```

2. Navigate and start Claude:

   ```bash
   cd ~/Developer/goodtogo-worktrees/agent-2
   claude
   ```

3. Install dependencies (first time only):

   ```bash
   pnpm install
   ```

4. Start development:

   ```bash
   pnpm dev
   ```

### Referencing Code from Other Branches

Use `/project:peek-branch` to view files without switching context:

```bash
# View file from main
/project:peek-branch main src/lib/services/some.service.ts

# View file from another feature branch
/project:peek-branch feature/other-pr package.json
```

Or use git directly:

```bash
# View file content
git show main:src/lib/types.ts

# Diff against main
git diff main -- src/lib/services/
```

### Coordinating Database Migrations

**CRITICAL**: All worktrees share the same database!

Before any schema change:

1. Check active worktrees:

   ```bash
   pnpm worktree:list
   ```

2. Coordinate with other developers/agents

3. Use safe migration command:

   ```bash
   pnpm db:migrate  # NOT prisma migrate dev directly
   ```

### Passing Work Between Agents

Use the handoff workflow:

1. **Source agent** creates handoff:

   ```bash
   /project:agent-handoff agent-2
   ```

2. **Target agent** receives handoff file in `.claude/handoffs/`

3. **Target agent** can load context:

   ```bash
   # Read the handoff file
   cat .claude/handoffs/202501101430-handoff.md

   # Or load a saved session
   /project:load-session
   ```

## Multi-Agent Coordination

### Spawning Agents in Worktrees (Recommended)

Instead of manually navigating to worktrees and starting Claude sessions, **orchestrate agents directly**:

```typescript
// From main repository, use Claude's Task tool to spawn an agent
Task({
  description: "Fix Issue #123 in worktree",
  subagent_type: "general-purpose",
  run_in_background: true,
  prompt: `
You are working in a git worktree at /path/to/goodtogo-worktrees/fix-123
on branch fix/issue-123.

IMPORTANT: Change to the worktree directory first:
cd /path/to/goodtogo-worktrees/fix-123

Your task: [Detailed task description]

After creating the PR, use the pr-shepherd skill to:
1. Monitor CI and handle failures autonomously
2. Respond to review comments and resolve all threads
3. Only escalate to orchestrator for complex issues requiring user input
4. Report back when PR is ready to merge or if blocked

Run autonomously - the orchestrator will check in via AgentOutputTool.
`,
});
```

**Key principle**: Agents own their PR lifecycle. The orchestrator spawns and moves on, checking back periodically rather than polling CI.

**Benefits**:

- Orchestrator remains free for other work (not blocked polling CI)
- Agents handle their own CI failures and review comments
- Can spawn multiple agents in parallel for different worktrees
- Agent output is captured and can be reviewed when ready

**Example workflow**:

```text
1. Create worktree: pnpm worktree:setup fix-123 fix/issue-123
2. Spawn agent with Task tool (run_in_background: true)
3. Continue other orchestrator work
4. Check agent status periodically: AgentOutputTool(block=false)
5. Agent handles CI, reviews, fixes autonomously
6. Retrieve final results when agent reports PR ready to merge
```

### Hub-and-Spoke Pattern

Recommended for complex features:

```text
Main Repository (Hub/Orchestrator)
├── Creates worktrees with pnpm worktree:setup
├── Spawns agents using Task tool (run_in_background: true)
├── Continues other work while agents run
├── Checks in periodically with AgentOutputTool(block=false)
├── Merges completed features
└── Coordinates database changes

Worktree: fix-123 (Spoke/Worker Agent)
├── Agent works in isolated directory
├── Creates PR when implementation done
├── Uses pr-shepherd skill to monitor CI
├── Handles review comments autonomously
├── Resolves all threads before reporting done
└── Reports back only when PR ready to merge OR blocked

Worktree: feature-456 (Spoke/Worker Agent)
├── Parallel agent works independently
├── Owns its own PR lifecycle
├── Handles CI failures and reviews
└── Reports back when ready or blocked
```

**The key insight**: Agents are autonomous workers, not just task executors. They own everything from implementation through PR merge readiness.

### Handoff Contracts

When handing off work, always include:

1. **What was accomplished** - Completed tasks
2. **What remains** - Specific next steps (not vague goals)
3. **Key decisions** - Why certain approaches were chosen
4. **Gotchas** - Things the next agent should know
5. **Test status** - Did tests pass? What needs testing?

### Avoiding Conflicts

| Shared Resource     | How to Coordinate                                           |
| ------------------- | ----------------------------------------------------------- |
| **Database schema** | Never migrate without checking other worktrees              |
| **Package.json**    | Commit lock files; let pnpm resolve                         |
| **Shared services** | Use interfaces; don't modify contracts without coordination |
| **Test data**       | Use unique identifiers per worktree                         |

## Database Safety

### Safe Commands

```bash
# These are safe
pnpm db:migrate           # Has worktree safety check
pnpm db:seed             # Uses environment isolation
pnpm prisma studio       # Read-only by default
```

### Dangerous Commands

```bash
# NEVER run these directly in a worktree
prisma migrate dev       # Bypasses safety checks
prisma migrate reset     # Would affect ALL worktrees
npx prisma db push       # Dangerous without coordination
```

### Migration Workflow

1. Coordinate with all active worktrees/agents
2. Run migration from main repository only
3. Other worktrees run `pnpm prisma generate` after migration

## Troubleshooting

### Port Conflicts

**Symptom**: `Error: listen EADDRINUSE: address already in use :::3000`

**Solution**:

```bash
# Find what's using the port
lsof -i :3000

# Kill it or use different port
PORT=3002 pnpm dev
```

### Redis Key Collisions

**Symptom**: Unexpected cache data or overwrites between worktrees

**Solution**: Ensure `REDIS_KEY_PREFIX` is set:

```bash
# Check current prefix
echo $REDIS_KEY_PREFIX

# Set if missing
export REDIS_KEY_PREFIX="$(basename $PWD):"
```

### Build Cache Problems

**Symptom**: Stale builds, incorrect types after switching branches

**Solution**:

```bash
# Clear Next.js cache
rm -rf .next

# Clear TypeScript cache
rm -rf node_modules/.cache

# Reinstall dependencies
pnpm install
```

### Stale Worktrees

**Symptom**: Old worktrees taking up space or causing confusion

**Solution**:

```bash
# List all worktrees
git worktree list

# Remove a stale worktree
git worktree remove ~/Developer/goodtogo-worktrees/old-feature

# Prune worktree references
git worktree prune
```

### Worktree Won't Create

**Symptom**: `fatal: 'branch-name' is already checked out at...`

**Cause**: Branch is checked out in another worktree

**Solution**:

```bash
# Create a new branch for this worktree
git worktree add ~/Developer/goodtogo-worktrees/new-wt -b new-branch-name

# Or check out a different branch in the existing worktree first
```

## Quick Reference Commands

| Command                                    | Purpose                                |
| ------------------------------------------ | -------------------------------------- |
| `/project:worktree-status`                 | Show current context and all worktrees |
| `/project:worktree-create <name> <branch>` | Create new worktree                    |
| `/project:peek-branch <branch> <file>`     | View file from another branch          |
| `/project:agent-handoff [target]`          | Create handoff document                |
| `git worktree list`                        | List all worktrees                     |
| `git worktree remove <path>`               | Remove a worktree                      |
| `git worktree prune`                       | Clean up stale worktree references     |

## See Also

- [Git Workflow Guide](./git-workflow.md) - Branch management and PR workflows
- [Session Management Guide](./session-management.md) - Saving and loading conversation context
- [Todo Management Guide](./todo-management.md) - Tracking work across sessions
