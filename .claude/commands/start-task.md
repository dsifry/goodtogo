# Start Task

Determine task complexity and use appropriate workflow for efficient development.

## Usage

```
/project:start-task <task-description>
```

## Steps

### 0. Pre-Task Checklist

Before starting any new task:

**Knowledge Priming (CRITICAL)**:

- [ ] Run BEADS prime with task keywords: `npx tsx scripts/beads-prime.ts --keywords "<task-keywords>" --work-type planning`
- [ ] Review MUST FOLLOW rules and GOTCHAS before proceeding
- [ ] Note any relevant patterns or decisions that constrain the approach

**PR Check**:

- [ ] Check if there are active PRs with pending comments
- [ ] Ask: "Before we start the new task, should we check if there are any PR comments to address?"
- [ ] If yes, run: `gh pr list --author @me --state open`
- [ ] Check each PR for new CodeRabbit comments

### 1. Task Assessment

**Use extended thinking** to analyze the task complexity before asking the user.

Consider:

- Number of files likely to be modified
- Whether database changes are needed
- Impact on existing functionality
- Testing requirements
- Integration points

Then ask the user to confirm your assessment:

> **Proposed complexity**: [Quick / Complex] ➜ Does this match your expectation?
>
> Based on my analysis, this task appears to be a [quick task that can be completed in < 2 hours / complex task requiring > 2 hours] because [brief reasoning].

Use this prompt template:

**Quick Task (< 2 hours, use streamlined flow):**

- Bug fixes
- Small UI tweaks
- Minor text/copy changes
- Simple configuration updates
- Adding basic validation
- Fixing linting/test issues

**Complex Task (> 2 hours, use full checklist):**

- New features with database changes
- New API endpoints
- Complex UI components
- Background job modifications
- Onboarding flow changes
- Multi-file refactoring
- Performance optimizations

### 2. Quick Task Flow

If user confirms it's a quick task:

#### Essential Steps

- [ ] Read relevant docs if unfamiliar with area
- [ ] Check existing patterns for similar functionality
- [ ] Make the change following existing patterns
- [ ] Write/update tests if logic changes
- [ ] Run `pnpm test --run && pnpm lint && pnpm build`
- [ ] Create simple PR with clear description
- [ ] Address review feedback

#### File Management

- [ ] Update `.claude/MANAGED_FILES.md` if creating files to preserve
- [ ] Clean up any temporary files created

### 3. Complex Task Flow

If it's a complex task:

- Use the full `.claude/project-checklist.md`
- Consider breaking into smaller tasks
- Use extended thinking for planning
- Create detailed implementation plan

### 4. Task Escalation

If a "quick task" becomes complex during implementation:

- Stop and reassess
- Switch to full checklist workflow
- Inform user of complexity change
- Consider breaking into multiple PRs

## Questions to Ask User

**Initial Assessment:**
"Is this a quick task (< 2 hours) or a complex task that requires the full development checklist?

Quick tasks include: bug fixes, small UI changes, simple configuration updates
Complex tasks include: new features, database changes, new API endpoints, background job modifications"

**If Uncertain:**
"This task involves [X]. This suggests it might be more complex than initially thought. Should we switch to the full checklist workflow?"
