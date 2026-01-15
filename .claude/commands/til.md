# Today I Learned (TIL)

Capture a learning or insight from the current conversation for future agents.

## Usage

```
/project:til <learning>
/project:til   # Interactive mode - will prompt for learning
```

## Examples

```
/project:til "PureDraftGenerationService needs two providers - stage1 for OpenAI, stage2 for Anthropic"
/project:til "The Thread model is for drafts only, not email threads - despite the name"
/project:til "Gmail API dates are RFC 2822 format - use parseGmailDate() helper"
```

## The Test: Would This Confuse a Naive Agent?

Before storing, ask yourself:

- Would a future agent, without our current context, benefit from knowing this?
- Is this codebase-specific (not generic programming knowledge)?
- Is this non-obvious (can't be found by just reading the code)?

**Good learnings:**

- Architectural decisions and their rationale
- Non-obvious system behaviors ("X does Y, not what you'd expect")
- Integration quirks specific to our stack
- Debugging insights that took time to discover

**Not learnings (don't capture):**

- Generic programming knowledge ("validate your inputs")
- Things obvious from reading the code
- Temporary workarounds that will be removed

## Steps

### 1. Parse the Learning

If `$ARGUMENTS` is provided, use it as the learning text.
If empty, ask the user:

> What did you learn that would help a future agent working on this codebase?

### 2. Classify the Learning

Ask the user to confirm or adjust:

```
I'll categorize this learning:

**Fact**: [extracted core insight]
**Type**: [pattern|gotcha|decision|api_behavior|security|performance]
**Applies to**: [file patterns or components]
**Confidence**: [high|medium|low]

Does this look right? (yes / edit)
```

**Type definitions:**

- `pattern` - How we do things here (conventions, preferred approaches)
- `gotcha` - Non-obvious behavior that causes bugs
- `decision` - Architectural choice and its rationale
- `api_behavior` - External API quirks (Gmail, Stripe, etc.)
- `security` - Security-related patterns or concerns
- `performance` - Performance considerations

### 3. Check for Conflicts

Search existing learnings for semantic overlap:

```bash
pnpm tsx scripts/knowledge-base.ts search --query "<learning-text>" --threshold 0.7
```

If similar learnings found, present them:

```
I found a potentially related learning:

**EXISTING** (from 2026-01-05, PR #876):
"PureDraftGenerationService uses a two-stage pipeline with different AI providers"

**NEW** (from this conversation):
"PureDraftGenerationService needs two providers - stage1 for OpenAI, stage2 for Anthropic"

These seem related. What should I do?

1. **New supersedes old** - The old learning is outdated
2. **Keep both** - They capture different aspects
3. **Merge** - Combine into one better learning
4. **Discard new** - The existing learning is sufficient
```

### 4. Store the Learning

Once confirmed, store with provenance:

```bash
pnpm tsx scripts/knowledge-base.ts store --learning '{
  "type": "<type>",
  "fact": "<the learning>",
  "context": "<when this applies>",
  "confidence": "<high|medium|low>",
  "tags": ["<tag1>", "<tag2>"],
  "provenance": {
    "source": "conversation",
    "reference": "<conversation-id or branch>",
    "date": "<today>",
    "author": "<user>"
  }
}'
```

### 5. Confirm Storage

```
Stored learning:

**[type]** (confidence: high)
> <the learning>

Context: <when this applies>
Tags: #tag1 #tag2

This will help future agents understand: <brief explanation>
```

## Conflict Resolution Guidelines

When conflicts arise, consider:

| Situation                              | Action                                |
| -------------------------------------- | ------------------------------------- |
| New learning is more specific/accurate | New supersedes old                    |
| Both capture different valid aspects   | Keep both, add distinguishing context |
| New learning contradicts old           | Ask user which is correct             |
| Old learning is a subset of new        | Merge into comprehensive learning     |

**The key question:** Would having both learnings confuse a naive agent, or would they complement each other?

## Provenance Tracking

Every learning tracks:

- **source**: "conversation" (this command), "session", "reflection", or "manual"
- **reference**: Conversation ID, PR number, or session file
- **date**: When captured
- **author**: Who validated it

This allows us to trace back to the original context if a learning is questioned.

## Integration with Workflow

**During debugging:**
When you discover why something was failing, capture it:

```
/project:til "Circuit breaker trips when OpenAI model name sent to Anthropic API - check provider routing"
```

**After PR review:**
If CodeRabbit or reviewer caught something non-obvious:

```
/project:til "Gmail pagination silently truncates at 100 results - always use nextPageToken"
```

**After architectural discussion:**
When a design decision is made:

```
/project:til "We use Redis for session storage because PostgreSQL was too slow for concurrent access patterns"
```

## Related Commands

- `/project:curate-pr-learnings` - Extract learnings from PR comments
- `/project:reflection` - Analyze conversation for improvements
- `/project:search-learnings` - Find relevant learnings (future)
