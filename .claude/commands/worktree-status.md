---
description: Show current worktree context and all active worktrees
---

# Worktree Status

Report the current worktree environment and list all active worktrees.

## Steps

1. **Detect current context**:

   ```bash
   echo "=== Current Environment ==="
   if [ -n "$WORKTREE_ID" ]; then
     echo "Worktree: $WORKTREE_ID"
     echo "Port: $PORT"
     echo "Redis Prefix: $REDIS_KEY_PREFIX"
   else
     echo "Location: Main repository"
     echo "Port: 3000"
   fi
   echo "Branch: $(git branch --show-current)"
   echo "Directory: $(pwd)"
   ```

2. **List all worktrees**:

   ```bash
   echo ""
   echo "=== All Worktrees ==="
   git worktree list
   ```

3. **Check running dev servers**:

   ```bash
   echo ""
   echo "=== Running Dev Servers (ports 3000-3100) ==="
   lsof -i :3000-3100 -sTCP:LISTEN 2>/dev/null | grep node || echo "No dev servers running"
   ```

4. **Report summary** to user with:
   - Current worktree context (or main repo)
   - Branch name
   - All active worktrees
   - Any running dev servers
