---
description: Create a new worktree for parallel development
---

# Create Worktree

Create a new git worktree for parallel development work.

## Usage

```
/project:worktree-create agent-2 feature/new-feature
```

## Arguments

- `name` - Identifier for the worktree (e.g., `agent-2`, `hotfix`, `experiment`)
- `branch` - Branch name to check out in the worktree

## Steps

1. **Validate not already in a worktree**:

   ```bash
   if [ -n "$WORKTREE_ID" ]; then
     echo "You're already in worktree: $WORKTREE_ID"
     echo "Create new worktrees from the main repository."
     exit 1
   fi
   ```

2. **Check if scripts exist**:

   ```bash
   if [ ! -f "bin/worktree-setup.sh" ]; then
     echo "Worktree scripts not found. Using git worktree directly."
   fi
   ```

3. **Run worktree setup**:

   ```bash
   # If pnpm script exists:
   pnpm worktree:setup "$NAME" "$BRANCH"

   # Otherwise, use git directly (derive path relative to repo location):
   REPO_DIR="$(git rev-parse --show-toplevel)"
   WORKTREE_DIR="${WORKTREES_DIR:-$(dirname "$REPO_DIR")/goodtomerge-worktrees}/$NAME"
   git worktree add "$WORKTREE_DIR" -b "$BRANCH" 2>/dev/null || \
   git worktree add "$WORKTREE_DIR" "$BRANCH"
   ```

4. **Report next steps**:
   - Worktree location
   - Port assigned (if using worktree scripts)
   - How to start Claude in new worktree:

     ```bash
     cd $WORKTREE_DIR  # Path shown in setup output
     claude
     ```

5. **Offer to create handoff** for the new agent

## Example Output

```
Worktree created successfully!

Location: /path/to/goodtomerge-worktrees/agent-2
Branch: feature/new-feature
Port: 3001
Redis Prefix: agent-2:

To start working in this worktree:
  cd /path/to/goodtomerge-worktrees/agent-2
  claude

Would you like me to create a handoff document for the new agent?
```

> **Note**: The actual path depends on where your main repository is located.
> Worktrees are created as siblings to the repo directory (e.g., if repo is at
> `~/Projects/goodtomerge`, worktrees go in `~/Projects/goodtomerge-worktrees/`).

## Notes

- **New branches always start from `main`** - This ensures PRs have clean diffs without unrelated changes
- Worktrees share the same Git repository but have separate working directories
- Each worktree gets an isolated port and Redis prefix (if using worktree scripts)
- Database is shared - coordinate schema changes carefully
- Always create worktrees from the main repository, not from another worktree
- To base a branch on something other than main, set `BASE_BRANCH=other-branch` before running
