# Create Pull Request

Create a comprehensive, well-documented pull request following Warmstart's standards and best practices.

## Usage

```
/project:create-pr <feature-branch-name>
```

## Steps

### 1. Pre-PR Checklist

#### Track Modified Files

```bash
# Get list of all modified files
git diff --name-only origin/main...HEAD

# Get TypeScript/JavaScript files only
MODIFIED_FILES=$(git diff --name-only origin/main...HEAD | grep -E '\.(ts|tsx|js|jsx)$')
echo "Modified files to validate: $MODIFIED_FILES"
```

#### Run Targeted Validation

- [ ] TypeScript check: `pnpm tsc --noEmit`
- [ ] ESLint on modified files:
  ```bash
  if [ -n "$MODIFIED_FILES" ]; then
    echo "$MODIFIED_FILES" | xargs -d '\n' pnpm eslint --max-warnings 0
  else
    echo "No modified JS/TS files to lint"
  fi
  ```
- [ ] Prettier on modified files:
  ```bash
  if [ -n "$MODIFIED_FILES" ]; then
    echo "$MODIFIED_FILES" | xargs -d '\n' pnpm prettier --check
  else
    echo "No modified JS/TS files to format check"
  fi
  ```
- [ ] Run tests: `pnpm test --run`
- [ ] Verify build: `pnpm build`
- [ ] Test onboarding flow if applicable
- [ ] Review your own code thoroughly first

### 2. PR Title Standards

Use conventional commit format:

- `feat: add LinkedIn profile enrichment to contact creation`
- `fix: resolve onboarding phase transition bug for users with <300 contacts`
- `refactor: optimize campaign scoring algorithm performance`
- `docs: update onboarding flow documentation`
- `test: add comprehensive coverage for draft manager component`

### 3. PR Description Template

```markdown
## Summary

Brief description of what this PR accomplishes and why it's needed.

## Changes Made

- [ ] Added/modified specific components or features
- [ ] Updated database schema (include migration details)
- [ ] Added/updated tests with coverage details
- [ ] Updated documentation

## Testing Done

- [ ] Unit tests: [X passing, Y total]
- [ ] Integration tests: [specific scenarios tested]
- [ ] Manual testing: [steps performed]
- [ ] Onboarding flow testing (if applicable)

## Database Changes

- [ ] Schema changes: [describe migrations]
- [ ] Data migrations: [if any]
- [ ] Backward compatibility: [confirmed/not applicable]

## Performance Impact

- [ ] No performance impact expected
- [ ] Performance improvements: [describe]
- [ ] Potential performance concerns: [describe and mitigation]

## Security Considerations

- [ ] No sensitive data exposed
- [ ] Authentication/authorization changes reviewed
- [ ] Input validation implemented

## Breaking Changes

- [ ] No breaking changes
- [ ] Breaking changes: [list and migration path]

## Related Issues

Closes #[issue-number]
Related to #[issue-number]

## Screenshots/Demo

[If UI changes, include before/after screenshots or demo links]
```

### 4. Code Review Preparation

- Self-review all changes line by line
- Add inline comments explaining complex logic
- Ensure commit messages are descriptive
- Remove any debug code, console.logs, or TODOs
- Verify all new code follows existing patterns

### 5. Create the PR

- Push branch and create PR via GitHub CLI or web interface
- Assign appropriate reviewers
- Add relevant labels (feature, bug, documentation, etc.)
- Link to related issues
- Request review from AI tools (CodeRabbit, Claude, etc.) if configured
