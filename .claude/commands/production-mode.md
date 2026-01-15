---
model: claude-sonnet-4-5-20250929
---

# Production Mode - Mandatory Safety Protocol for Production Systems

**⚠️ USE THIS WHEN WORKING WITH PRODUCTION SYSTEMS ⚠️**

This mode is designed for when you ARE touching production servers, databases, or live systems. It provides critical safety guardrails to prevent accidental damage through strict read-only enforcement and active command blocking.

**If you're SSHed into a production server or running commands against production infrastructure, ACTIVATE THIS MODE FIRST.**

## 🚨 CRITICAL SAFETY RULES 🚨

When production mode is active, Claude will:

- **ACTIVELY REFUSE** to provide any destructive commands
- **REQUIRE** environment setup (`cd /home/ubuntu/goodtogo && source .env`) before operations
- **ONLY PROVIDE** read-only commands for viewing, monitoring, and analysis
- **BLOCK** any file modifications, service restarts, database writes, or state changes

## Usage

```
/project:production-mode [on|off]
```

- `on` or no argument: **Activates production safety protocol** - Use this when you're about to work with production systems
- `off`: Deactivates production mode when you return to local development

**Best Practice**: Activate production mode BEFORE you SSH into production servers or run any commands against production infrastructure.

## What Production Mode Does

Production mode transforms Claude's behavior to enforce strict safety when working with live production systems:

### 1. Safety Enforcement

**BLOCKED COMMANDS** (Claude will refuse to provide these):

**File Operations:**

- ❌ `vim`, `nano`, `ed`, `emacs` - No file editing
- ❌ `sed -i`, `awk` with write - No in-place modifications
- ❌ `>`, `>>`, `tee` - No file writing
- ❌ `echo >`, `cat >` - No output redirection to files
- ❌ `rm`, `unlink`, `rmdir` - No deletions
- ❌ `mv`, `cp` with destructive intent - No moves/copies that overwrite
- ❌ `chmod`, `chown` - No permission changes

**Service Operations:**

- ❌ `systemctl restart/stop/start` - No service control
- ❌ `service restart/stop/start` - No service control
- ❌ `kill`, `pkill`, `killall` - No process killing
- ❌ Stopping Next.js process - No application restarts

**Code/Build Operations:**

- ❌ `npm install`, `pnpm install` - No dependency changes
- ❌ `pnpm build`, `npm run build` - No building on production
- ❌ `git commit`, `git push`, `git pull` - No git modifications
- ❌ `git merge`, `git rebase` - No git operations
- ❌ Running TypeScript scripts that modify data
- ❌ Crontab modifications (`crontab -e`)

**Database Operations:**

- ❌ `INSERT`, `UPDATE`, `DELETE` - No data modifications
- ❌ `DROP`, `ALTER`, `CREATE` - No schema changes
- ❌ `TRUNCATE` - No data deletion
- ✅ `SELECT` ONLY - Read-only queries allowed

### 2. Allowed Read-Only Operations

**Viewing Files:**

```bash
cat, tail, head, less, more, grep, find, ls, tree
```

**Monitoring:**

```bash
ps aux, top, htop, df -h, du -sh, netstat, ss
```

**Service Status (NO RESTARTS):**

```bash
systemctl status, crontab -l, git status, git log, git diff
```

**Database (SELECT ONLY):**

```bash
psql $DATABASE_URL -c "SELECT ..."
```

**Logs:**

```bash
tail -f logs/*.log, journalctl -u service-name
```

### 3. Standard Production Workflow

#### Step 1: Environment Setup (ALWAYS FIRST)

```bash
┌─[PRODUCTION SETUP - REQUIRED FIRST STEP]────────┐
│ cd /home/ubuntu/goodtogo && source .env       │
└──────────────────────────────────────────────────┘
```

#### Step 2: Investigation Commands

After sourcing environment, Claude will provide read-only investigation commands.

#### Step 3: Changes (IF NEEDED)

```
🚫 DEVELOPMENT REQUIRED 🚫
Changes must be made locally following this workflow:
1. Develop changes locally
2. Test thoroughly with pnpm lint && pnpm typecheck && pnpm test --run
3. Create PR with full validation
4. Review and merge to main
5. Deploy via standard process (see .claude/CLAUDE.local.md)
```

## Production Mode Features

### Visual Banner

Every response starts with:

```
🔴 [PRODUCTION MODE ACTIVE - READ-ONLY ENFORCEMENT] 🔴
═══════════════════════════════════════════════════════════
Server: [Detected from context]
Working Dir: /home/ubuntu/goodtogo
Environment: MUST be sourced before operations
═══════════════════════════════════════════════════════════
⚠️  ALL DESTRUCTIVE COMMANDS BLOCKED
✅  ONLY READ-ONLY OPERATIONS ALLOWED
═══════════════════════════════════════════════════════════
```

### Command Format

Commands presented in numbered boxes with expected output:

```
┌─[PRODUCTION COMMAND #1 - READ-ONLY]─────────────┐
│ cd /home/ubuntu/goodtogo && source .env       │
│ tail -n 50 logs/cron.log                       │
└──────────────────────────────────────────────────┘
Expected: Last 50 lines of cron log output
```

### Server-Specific Context

Production mode loads server-specific information from `.claude/CLAUDE.local.md`:

- **goodtogo.ai**: Next.js web application server
- **inboxprocessor**: Email processing and cron jobs
- **redis/puppeteer**: Redis cache and Puppeteer services

### Database Access Pattern

For database queries (SELECT only):

```bash
┌─[DATABASE QUERY - SELECT ONLY]──────────────────┐
│ cd /home/ubuntu/goodtogo && source .env       │
│ psql $DATABASE_URL -c "SELECT id, email        │
│   FROM \"User\" WHERE active = true LIMIT 10;" │
└──────────────────────────────────────────────────┘
```

**Automatic Blocking:**

- Any query containing INSERT/UPDATE/DELETE will be refused
- Claude will explain why and suggest read-only alternatives

## Destructive Command Detection

If you request a destructive operation, Claude will:

1. **Refuse to provide the command**
2. **Explain why it's blocked**
3. **Provide the local development workflow**
4. **Suggest read-only alternatives** for investigation

**Example:**

```
❌ REQUEST BLOCKED ❌

You asked: "Restart the Next.js server on goodtogo.ai"

⛔ This is a DESTRUCTIVE operation that modifies production state.

✅ CORRECT APPROACH:
1. If there's an issue, investigate with read-only commands first
2. For intentional restarts, this is a deployment operation
3. See .claude/CLAUDE.local.md for manual deployment procedure
4. Never restart services via Claude - requires manual intervention

🔍 INVESTIGATION ALTERNATIVES:
- Check process status: ps aux | grep next
- View application logs: tail -f logs/app.log
- Check system resources: top, df -h
```

## Initial Discovery Commands

On first activation, Claude provides:

**System Overview:**

```bash
# Environment setup
cd /home/ubuntu/goodtogo && source .env

# System information
uname -a
df -h
free -h

# Application status
ps aux | grep -E "node|next"
git log -1 --oneline
cat package.json | grep version

# Service status (NO RESTARTS)
systemctl status nginx
crontab -l

# Recent logs
tail -20 logs/cron.log
tail -20 logs/job.log
```

## Context Storage

Production environment details stored _during this session_ in `.claude/production-context.md` include:

- Current server and role
- Application version and branch
- Service status (for reference, not modification)
- Recent log patterns
- Environment variables (names only, not values)

**Note**: `.claude/production-context.md` captures dynamic session state (version, current logs); `.claude/CLAUDE.local.md` contains static local-only deployment guidance.

## Example Production Session

**Typical workflow when investigating a production issue:**

```
User: [SSHs into goodtogo.ai production server]
User: /project:production-mode

Claude: 🔴 [PRODUCTION MODE ACTIVE - READ-ONLY ENFORCEMENT] 🔴
        [Shows banner and initial discovery commands]

User: [Provides output from goodtogo.ai server]

Claude: [Analyzes, provides context-aware read-only commands]

User: I need to check the job queue status on inboxprocessor

Claude: [Provides safe commands to check job queue, logs, and status]

User: Can you restart the job queue?

Claude: ❌ REQUEST BLOCKED - Service restarts require manual intervention.
        I can help investigate issues with read-only commands.
        See .claude/CLAUDE.local.md for deployment procedures.

User: [Logs out of production server]
User: /project:production-mode off

Claude: Production mode deactivated. Returning to local development.
```

## Best Practices

1. **Always start with environment setup**: `cd /home/ubuntu/goodtogo && source .env`
2. **Provide complete outputs** including errors and warnings
3. **Redact sensitive data** like API keys, passwords, tokens
4. **Mention unexpected behavior** if commands produce unusual results
5. **Trust the safety blocks** - if Claude refuses a command, it's for good reason

## When to Use Production Mode

✅ **REQUIRED FOR:**

- **ANY time you're SSH'd into a production server**
- **ANY time you're running commands against production infrastructure**
- Investigating production issues
- Viewing logs and monitoring
- Checking application/service status
- Running read-only database queries
- Understanding production system state
- Troubleshooting live system problems

🛡️ **PROTECTION PROVIDED:**

Production mode actively blocks you from:

- Making any changes to production
- Deploying code
- Restarting services
- Modifying configuration
- Running scripts that change state
- Accidentally breaking things

**For all changes**: Develop locally → PR → Review → Deploy

**Remember**: If you're touching production infrastructure, this mode should be ON. It's not restrictive - it's protective.

## Production Mode Persistence

Remains active until:

- You run `/project:production-mode off`
- You say "exit production mode"
- The conversation ends

## Emergency Response Protocol

If you discover a critical production issue:

```
🚨 CRITICAL ISSUE DETECTED 🚨

1. ✅ Document thoroughly (screenshots, logs, errors)
2. ✅ Use read-only commands to gather diagnostic info
3. ❌ DO NOT attempt to fix on production
4. ✅ Report via proper channels (Slack, email, PagerDuty)
5. ✅ Create hotfix branch LOCALLY
6. ✅ Test locally with full validation
7. ✅ Fast-track PR with "HOTFIX:" prefix
8. ✅ Deploy after review (even hotfixes need review)
```

## Loading Production Context

Production-specific details are in `.claude/CLAUDE.local.md` including:

- Server hostnames and SSH configuration
- Deployment procedures for each server
- Service details and architecture
- Cron job schedules and purposes
- Emergency contact information

This file is LOCAL-ONLY and never committed to git.
