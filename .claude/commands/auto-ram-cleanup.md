---
model: claude-haiku-4-5-20251001
---

# Automatic RAM Cleanup

You are a system administrator performing automatic cleanup of wasteful development processes. This command runs WITHOUT user confirmation for safe-to-kill processes.

## Execution Steps

1. **Check Current Memory**:

   ```bash
   # Get memory stats before cleanup
   vm_stat | head -10
   ```

2. **Identify and Kill Safe Targets**:

   Kill these process types automatically (no confirmation needed):

   ### Test Runners (Always Safe)

   ```bash
   # Vitest processes
   pkill -f "vitest" 2>/dev/null && echo "Killed vitest processes" || true

   # Jest processes
   pkill -f "jest" 2>/dev/null && echo "Killed jest processes" || true

   # Playwright test processes
   pkill -f "playwright" 2>/dev/null && echo "Killed playwright processes" || true
   ```

   ### Old/Orphaned Development Tools

   ```bash
   # TypeScript language server instances (keep newest, kill old)
   # Find tsserver processes older than 2 hours
   pgrep -f "tsserver" | while read pid; do
     age=$(ps -o etimes= -p $pid 2>/dev/null | tr -d ' ')
     if [ -n "$age" ] && [ "$age" -gt 7200 ]; then
       kill $pid 2>/dev/null && echo "Killed old tsserver (PID $pid, age ${age}s)"
     fi
   done

   # Old typescript processes
   pgrep -f "typescript" | while read pid; do
     age=$(ps -o etimes= -p $pid 2>/dev/null | tr -d ' ')
     if [ -n "$age" ] && [ "$age" -gt 7200 ]; then
       kill $pid 2>/dev/null && echo "Killed old typescript process (PID $pid)"
     fi
   done
   ```

   ### Cursor/Editor Orphans

   ```bash
   # Cursor helper processes that are orphaned (parent PID 1)
   pgrep -f "Cursor Helper" | while read pid; do
     ppid=$(ps -o ppid= -p $pid 2>/dev/null | tr -d ' ')
     if [ "$ppid" = "1" ]; then
       kill $pid 2>/dev/null && echo "Killed orphaned Cursor Helper (PID $pid)"
     fi
   done

   # Old Cursor extension host processes (> 4 hours)
   pgrep -f "extensionHost" | while read pid; do
     age=$(ps -o etimes= -p $pid 2>/dev/null | tr -d ' ')
     if [ -n "$age" ] && [ "$age" -gt 14400 ]; then
       kill $pid 2>/dev/null && echo "Killed old extensionHost (PID $pid)"
     fi
   done
   ```

   ### Build Tool Orphans

   ```bash
   # Orphaned esbuild processes
   pkill -f "esbuild.*service" 2>/dev/null && echo "Killed esbuild service processes" || true

   # Orphaned webpack processes
   pgrep -f "webpack" | while read pid; do
     ppid=$(ps -o ppid= -p $pid 2>/dev/null | tr -d ' ')
     if [ "$ppid" = "1" ]; then
       kill $pid 2>/dev/null && echo "Killed orphaned webpack (PID $pid)"
     fi
   done
   ```

   ### Dev Servers (End of Session Cleanup)

   ```bash
   # Next.js dev server
   pkill -f "next-server" 2>/dev/null && echo "Killed next-server processes" || true
   pkill -f "next dev" 2>/dev/null && echo "Killed next dev processes" || true

   # pnpm/npm dev processes
   pkill -f "pnpm.*dev" 2>/dev/null && echo "Killed pnpm dev processes" || true
   pkill -f "npm.*run.*dev" 2>/dev/null && echo "Killed npm dev processes" || true
   ```

   ### Job Queue Workers

   ```bash
   # run-job-queue processes
   pkill -f "run-job-queue" 2>/dev/null && echo "Killed run-job-queue processes" || true

   # tsx watch processes for job queues
   pkill -f "tsx.*watch.*run-job-queue" 2>/dev/null && echo "Killed tsx job queue watchers" || true
   ```

   ### Node.js Zombies

   ```bash
   # Node processes in zombie state
   ps aux | grep -E "node.*<defunct>" | awk '{print $2}' | xargs -r kill -9 2>/dev/null && echo "Killed zombie node processes" || true
   ```

3. **Check Memory After Cleanup**:

   ```bash
   # Get memory stats after cleanup
   vm_stat | head -10
   ```

4. **Report Summary**:

   Provide a brief summary:
   - Number of processes killed by category
   - Estimated memory freed (if measurable)
   - Any processes that were protected

## PROTECTED PROCESSES (Never Kill)

These must NEVER be terminated:

- **Claude**: Any process with "claude" in the name
- **Docker**: `docker`, `dockerd`, `com.docker`, `Docker Desktop`
- **System Services**: Anything under `/System/`, `/usr/libexec/`, launchd, kernel_task
- **Database Services**: `postgres`, `mysql`, `redis`, `mongod`

## Safety Checks

Before killing ANY process, verify:

1. It's NOT in the protected list above
2. It's NOT the user's active terminal session
3. For age-based kills: process must be older than threshold

## Output Format

```text
🧹 Auto RAM Cleanup

Before: [X]% memory pressure
Killed:
  - vitest: 3 processes
  - dev servers: 2 processes
  - run-job-queue: 1 process
  - old tsserver: 2 processes (> 2h old)
  - orphaned Cursor Helper: 1 process

After: [Y]% memory pressure
Freed: ~[Z] MB (estimated)

Protected (not touched):
  - Docker: 4 processes
  - claude: 2 processes
```
