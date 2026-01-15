---
model: claude-haiku-4-5-20251001
---

# /project:announce-pr

> ⚠️ **Note**: `/project:announce-pr` is a Claude slash command.
> Type it directly into the chat interface. Attempting to run it in Bash or a
> shell will fail with "no such file or directory".

Generate a Slack message to announce a PR to reviewers with all necessary context.

## Usage

```
/project:announce-pr <pr-number>
```

## Description

This command generates a well-structured Slack message for announcing PRs to your team. It includes:

- PR URL and purpose
- Focus areas for reviewers
- Tricky or complex sections
- Open issues/questions
- Clear call to action

## Workflow

### 1. Gather PR Information

```bash
# Get PR details (only essential fields to avoid large outputs)
gh pr view <pr-number> --json title,url

# Check changed files count and summary
gh pr diff <pr-number> --stat | tail -5

# Check CI status
gh pr checks <pr-number>

# For detailed file list (if needed), limit output
gh pr view <pr-number> --json files | jq -r '.files[:10][].path'
```

### 2. Slack Message Template

```markdown
Hey team! 👋

I've just opened PR #<NUMBER> that <BRIEF_DESCRIPTION>: <PR_URL>

**Purpose**: <2-3 sentences explaining WHY this PR exists and what problem it solves>

**Please focus on**:

- <Specific area 1> - <why this needs attention>
- <Specific area 2> - <what to look for>
- <Specific area 3> - <potential concerns>

**Potentially tricky areas**:

- <Complex section 1> - <brief explanation of complexity>
- <Edge case or assumption> - <what might not be obvious>

**Still open**:

- <Question or undecided approach 1>
- <Area that might need iteration>

<OPTIONAL: Performance/Security note if relevant>

This <affects/is> <scope: e.g., "is all documentation", "affects the LinkedIn processing pipeline", "touches auth flow">. Would really appreciate your eyes on this to <specific ask: e.g., "ensure the logic is sound", "validate the approach", "check for edge cases I missed">! 🙏
```

### 3. Message Variations by PR Type

#### Feature PRs

```markdown
Hey team! 👋

I've just opened PR #<NUMBER> that implements <FEATURE_NAME>: <PR_URL>

**Purpose**: This adds <capability> to address <user need/pain point>. <Additional context about why now>.

**Please focus on**:

- The <core algorithm/logic> - does this handle all the edge cases?
- The API design - is this intuitive for other developers?
- Performance implications - any concerns about scale?

**Potentially tricky areas**:

- <Integration point> - I had to work around <existing limitation>
- The <specific implementation> assumes <assumption> - let me know if this seems reasonable

**Still open**:

- Should we add <additional feature/safety check>?
- The <specific choice> could also be done via <alternative> - thoughts?

This touches <N> files across <components>. Would love your thoughts on the overall approach! 🙏
```

#### Bug Fix PRs

```markdown
Hey team! 👋

I've just opened PR #<NUMBER> that fixes <BUG_DESCRIPTION>: <PR_URL>

**Purpose**: Users were experiencing <symptom> when <condition>. This was caused by <root cause>.

**Please focus on**:

- The fix in <file/component> - does this fully address the issue?
- Regression risk - could this break existing functionality?
- Test coverage - are the new tests comprehensive enough?

**Potentially tricky areas**:

- The fix required changing <shared component> which is used by <other features>
- I had to handle <edge case> which wasn't documented

**Still open**:

- Should we backport this to <version>?
- Is the error handling sufficient for <scenario>?

This is a targeted fix affecting <scope>. Please check if I've missed any side effects! 🙏
```

#### Refactor PRs

```markdown
Hey team! 👋

I've just opened PR #<NUMBER> that refactors <COMPONENT/SYSTEM>: <PR_URL>

**Purpose**: The existing <code> was becoming difficult to <maintain/extend/test> due to <specific issues>. This refactor <improvement achieved>.

**Please focus on**:

- Behavior preservation - I've tried to keep all functionality identical
- The new structure - is this clearer and more maintainable?
- Performance - the benchmarks show <results>, but please verify

**Potentially tricky areas**:

- <Migration aspect> - existing <data/state> needs to be handled carefully
- The <abstraction> might be <too general/too specific> - open to feedback

**Still open**:

- Should we deprecate <old API> immediately or phase it out?
- The naming of <concept> - any better suggestions?

This is a large refactor touching <N> files. All tests pass but extra eyes on the logic flow would be great! 🙏
```

#### Documentation PRs

```markdown
Hey team! 👋

I've just opened PR #<NUMBER> that <updates/adds> documentation for <TOPIC>: <PR_URL>

**Purpose**: <Users/Developers> were struggling to understand <concept/process>. This documentation <clarifies/explains/guides>.

**Please focus on**:

- Technical accuracy - are all the details correct?
- Clarity - is this understandable for our target audience?
- Completeness - am I missing any important scenarios?

**Potentially tricky areas**:

- The <technical concept> explanation - I tried to balance detail with accessibility
- The examples - are these representative of real usage?

**Still open**:

- Should we add more <examples/diagrams/warnings>?
- Is the organization intuitive?

This is documentation only - no code changes. Would appreciate a review for accuracy and clarity! 🙏
```

### 4. Tips for Effective PR Announcements

#### DO's

- ✅ Be specific about what you want reviewed
- ✅ Highlight areas of uncertainty
- ✅ Mention the scope/impact clearly
- ✅ Include PR number and URL prominently
- ✅ Use formatting to make it scannable
- ✅ End with a clear ask

#### DON'T's

- ❌ Write novels - keep it concise
- ❌ Be vague about focus areas
- ❌ Forget to mention breaking changes
- ❌ Assume context - provide it
- ❌ Use too much technical jargon

### 5. Example Usage Flow

```bash
# 1. Create PR first
gh pr create --title "feat: add LinkedIn enrichment" --body "..."

# 2. Get PR number
PR_NUMBER=$(gh pr view --json number -q .number)

# 3. Generate announcement
/project:announce-pr $PR_NUMBER

# 4. Copy the generated message and paste in Slack
# 5. Tag relevant reviewers in Slack thread
```

### 6. Quick Copy Templates

#### Minimal Template

```
PR #<NUMBER>: <TITLE>
<URL>

<WHAT>: <1 sentence>
<WHY>: <1 sentence>
<FOCUS>: <main review point>

Thanks for reviewing! 🙏
```

#### Standard Template

```
Hey team! 👋

PR #<NUMBER>: <URL>

**What**: <description>
**Why**: <motivation>

**Please check**:
- <area 1>
- <area 2>

**Questions**: <any open items>

Appreciate the review! 🙏
```

## Related Commands

- `/project:create-pr` - Create the PR itself
- `/project:handle-pr-comments` - Respond to PR feedback
- `/project:review-pr` - Review others' PRs
