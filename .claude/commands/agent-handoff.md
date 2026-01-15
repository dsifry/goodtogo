---
description: Save context for handoff to another agent or session
---

# Agent Handoff

Save current session context for another agent to continue work.

## Usage

```
/project:agent-handoff              # Save for any agent
/project:agent-handoff agent-2      # Save specifically for agent-2 worktree
```

## Arguments

- `target_worktree` (optional) - Name of the target worktree to copy handoff to

## Steps

1. **Gather current context**:
   - Current branch: `git branch --show-current`
   - Modified files: `git status --porcelain`
   - Current worktree (if any): `$WORKTREE_ID`
   - Open PRs on this branch: `gh pr list --head $(git branch --show-current)`

2. **Create handoff directory**:

   ```bash
   HANDOFF_DIR=".claude/handoffs"
   mkdir -p "$HANDOFF_DIR"
   HANDOFF_FILE="$HANDOFF_DIR/$(date +%Y%m%d%H%M)-handoff.md"
   ```

3. **Write handoff content** (template below)

4. **If target worktree specified**, copy handoff there:

   ```bash
   # Derive worktrees directory relative to repo root
   REPO_DIR="$(git rev-parse --show-toplevel)"
   WORKTREES_DIR="${WORKTREES_DIR:-$(dirname "$REPO_DIR")/goodtogo-worktrees}"
   TARGET_DIR="$WORKTREES_DIR/$TARGET_WORKTREE"
   if [ -d "$TARGET_DIR" ]; then
     mkdir -p "$TARGET_DIR/.claude/handoffs"
     cp "$HANDOFF_FILE" "$TARGET_DIR/.claude/handoffs/"
   fi
   ```

5. **Report handoff location** to user

## Handoff Template

````markdown
# Agent Handoff - [timestamp]

## Source

- Worktree: [current worktree or "main repository"]
- Branch: [branch name]
- Directory: [pwd]

## Current Task

[Ask user to describe or infer from recent work]

## Progress

- [x] Completed items
- [ ] Remaining items

## Modified Files

[git status output]

## Key Decisions Made

[Important context that would be lost without this document]

## Next Steps

1. [Specific next action]
2. [Following action]
3. [Additional steps]

## How to Continue

```bash
cd [target directory]
claude
# Then: /project:load-session or read this handoff file
```
````

## Example Interaction

```text
User: /project:agent-handoff agent-2

Claude: I'll create a handoff document for agent-2.

Current context:

- Branch: feature/worktree-infrastructure
- Worktree: main repository
- Modified files: 3 files changed

Please briefly describe the current task and what remains to be done:

> [User provides description]

Handoff created at:
.claude/handoffs/202501101430-handoff.md

Also copied to:
~/Developer/goodtogo-worktrees/agent-2/.claude/handoffs/

To continue in agent-2:
cd ~/Developer/goodtogo-worktrees/agent-2
claude
```

## Notes

- Handoffs are ephemeral and should be gitignored
- Include enough context that the receiving agent can continue without this session
- Key decisions and "why" reasoning is more important than implementation details
- Always list specific next steps, not vague goals
