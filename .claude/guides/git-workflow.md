# Git Workflow Guide

This guide covers Git best practices, branch management, commit conventions, and PR workflows for the Warmstart codebase.

## Current Branch Awareness

**🚨 CRITICAL**: Always maintain awareness of your current branch to prevent wrong-branch operations.

Before ANY git operation (add, commit, push, checkout), you MUST:

```bash
# 1. Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# 2. Verify it matches your intention
# If working on a PR, ensure branch name matches the PR

# 3. Check if PR exists for this branch
gh pr list --head "$CURRENT_BRANCH" --state open
```

Common branch confusion scenarios to avoid:

- Pushing to main instead of feature branch
- Creating PR from wrong branch
- Committing fixes to unrelated branch
- Losing track after multiple git operations

## Git Commit Attribution and PR Workflow

### Pre-Commit Verification

Before ANY git operations:

1. **Verify current branch**: `git branch --show-current`
2. **Check for uncommitted changes**: `git status`
3. **Review changes**: `git diff` (unstaged) or `git diff --cached` (staged)
4. **Run validation on modified files**:

   ```bash
   # Get list of modified TypeScript/JavaScript files
   MODIFIED_FILES=$(git diff --name-only --diff-filter=ACM | grep -E '\.(ts|tsx|js|jsx)$')

   # Run ESLint
   if [ -n "$MODIFIED_FILES" ]; then
     echo "$MODIFIED_FILES" | xargs pnpm eslint --max-warnings 0
   fi

   # Run TypeScript check
   pnpm tsc --noEmit

   # Run tests if any test files were modified
   if echo "$MODIFIED_FILES" | grep -q '\.test\.' || echo "$MODIFIED_FILES" | grep -q '\.spec\.'; then
     pnpm test --run
   fi
   ```

### Commit Guidelines

When making commits with Claude's assistance:

- **DO**: Include `🤖 Generated with Claude Code` in commit messages
- **DO**: Use `Co-Authored-By: Claude (AI Assistant)` for attribution
- **DO**: Group related changes into logical commits
- **DON'T**: Include email addresses in the Co-Authored-By line (GitHub may strip this line, but the 🤖 indicator ensures transparency)
- **DON'T**: Create commits without running validation first

### PR Creation Workflow

1. **Verify branch**: `git branch --show-current`
2. **Push branch**: `git push origin <branch-name>`
3. **Create PR with comprehensive description**:
   ```bash
   gh pr create --title "feat: clear description" --body "..."
   ```
4. Include in PR description:
   - Summary with before/after metrics
   - Detailed list of changes
   - Review focus areas
   - Testing confirmation
   - Any remaining work

📝 **Multi-file commits**: See multi-file commit strategy section below

Example commit message:

```
feat: add LinkedIn processing enhancements

- Implement smart caching for API optimization
- Add sales intelligence analysis
- Improve name validation logic

🤖 Generated with Claude Code

Co-Authored-By: Claude (AI Assistant)
```

## PR Comment Monitoring Workflow

Claude will remind you to check for PR comments **only when working on existing PRs** at these key moments:

1. **After completing significant work on an existing PR, before committing** - When multiple files have been modified and a PR already exists: "We've made several changes to this PR. Before we commit, would you like me to check for any new comments?"
2. **After pushing updates to an existing PR** - When `git push` completes successfully on a branch with an open PR: "I've pushed the changes. Would you like me to check for any new PR comments?"
3. **Before switching away from a PR branch** - Before running `git checkout` from a branch with an open PR: "Before switching branches, should we check if there are any PR comments to address?"
4. **Before starting new tasks** - Only if you have open PRs: "Before we start this new task, should we check for any pending feedback on your open PRs?"

### When This Workflow Applies

This workflow **only applies when**:

- A PR has already been created and pushed to GitHub
- You're making additional changes to an existing PR
- You have open PRs that might have received feedback

This workflow **does not apply when**:

- Working on initial feature development before creating a PR
- Making changes on a branch that hasn't been pushed yet
- Working on a branch without an associated PR

### Example Timing Pattern

For an existing PR with ongoing work:

```markdown
1. Working on PR #XXX (already exists on GitHub)
2. Complete implementation work (multiple files changed)
3. Claude asks: "We've made several changes to this PR. Before we commit, would you like me to check for any new comments?"
4. Review and address any feedback
5. Commit the changes including any fixes
6. Push to origin
7. Check again for any new comments after push
```

## Checking for Comments (Your PRs Only)

```bash
# List YOUR open PRs
gh pr list --author @me --state open

# Quick check for new comments on YOUR PR
gh pr view <pr-number> --json comments,reviews | jq -r '.comments | length'

# View all review comments on YOUR PR
gh api repos/{owner}/{repo}/pulls/<pr-number>/comments

# Check inline code comments on YOUR PR
gh api repos/{owner}/{repo}/pulls/<pr-number>/comments | jq -r '.[] | "\(.path):\(.line) - \(.body)"'
```

## Resolving Comments Workflow

For detailed guidance on handling PR comments, including response templates and attribution requirements, use:

```
/project:handle-pr-comments <pr-number>
```

**Note**: This is a Claude slash command - type it in the chat, do not try to execute it via Bash/shell.

This command provides:

- Response templates for different types of feedback
- Proper attribution format (Claude on behalf of user)
- Guidelines for when to mark comments as resolved
- Best practices for professional code review responses

**Important**: We only check and address comments on PRs that you authored. We never modify other people's PRs unless explicitly asked.

## Multi-File Commit Strategy

When working with multiple files, consider these strategies:

### Strategy 1: Single Comprehensive Commit

Best for: Related changes across multiple files

```bash
git add .
git commit -m "feat: implement user profile enhancements

- Add avatar upload functionality
- Update profile validation logic
- Enhance UI components

🤖 Generated with Claude Code

Co-Authored-By: Claude (AI Assistant)"
```

### Strategy 2: Logical Commit Grouping

Best for: Large features with distinct components

```bash
# Backend changes
git add src/api/* src/lib/*
git commit -m "feat(api): add profile endpoint logic"

# Frontend changes
git add src/components/* src/hooks/*
git commit -m "feat(ui): implement profile components"

# Tests
git add **/*.test.ts
git commit -m "test: add profile feature tests"
```

### Strategy 3: File-by-File Commits

Best for: Unrelated changes or debugging

```bash
git add src/lib/profile.ts
git commit -m "fix: resolve null reference in profile loader"

git add src/components/ProfileForm.tsx
git commit -m "style: improve form layout consistency"
```

## Common Git Commands

### Working with Branches

```bash
# Create and switch to new branch
git checkout -b feature/branch-name

# List all branches
git branch -a

# Delete local branch
git branch -d branch-name

# Update branch from main
git checkout main
git pull origin main
git checkout feature/branch-name
git rebase main
```

### Stashing Changes

```bash
# Save current changes
git stash

# List stashes
git stash list

# Apply most recent stash
git stash pop

# Apply specific stash
git stash apply stash@{2}
```

### Undoing Changes

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Amend last commit
git commit --amend
```

## Best Practices

1. **Commit Frequently**: Make small, logical commits
2. **Write Clear Messages**: Use conventional commit format
3. **Review Before Push**: Always review changes before pushing
4. **Keep Branches Updated**: Regularly sync with main branch
5. **Clean Up**: Delete merged branches locally and remotely

## See Also

- @.claude/commands/handle-pr-comments.md for PR comment handling
- @.claude/commands/create-pr.md for PR creation workflow
- @.claude/development-workflow.md for file tracking patterns
