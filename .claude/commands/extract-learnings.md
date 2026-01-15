# Extract Learnings from Conversation

Analyze conversation history (current session + historical JSONL files) to identify strategic insights worth capturing for future agents.

## Usage

```text
/project:extract-learnings [options]
```

Options:

- `--current` - Only analyze current context window (fast)
- `--historical` - Also mine recent JSONL conversation files (thorough)
- `--recent N` - How many historical sessions to analyze (default: 3)

## When to Use

- At the end of a significant debugging session
- After making architectural decisions
- Before context compaction (when conversation is getting long)
- After resolving a tricky issue
- Before ending a multi-hour session

## Steps

### 1. Gather Conversation Data

**A. Current Context Analysis**
Review the conversation in your context window, looking for strategic patterns.

**B. Historical Session Mining** (if `--historical` flag or default)
Run the extraction script to get summaries and strategic content:

```bash
# Get conversation summaries (high-level strategic context)
pnpm tsx scripts/conversation-history.ts summaries --recent 5

# Extract strategic dialogue from recent sessions
pnpm tsx scripts/conversation-history.ts extract --strategic-only --recent 3
```

### 2. Identify Strategic Patterns

Look for these high-value patterns across both current and historical context:

**Architectural Decisions:**

- "We decided to..." / "The approach is..."
- "We're using X instead of Y because..."
- Trade-offs discussed and conclusions reached
- Design patterns chosen and rationale

**Debugging Insights:**

- "The problem was..." / "The root cause was..."
- "It turns out that..." / "What actually happens is..."
- Moments where understanding shifted
- Multi-hour debugging sessions that revealed non-obvious issues

**Non-Obvious Behaviors:**

- "Despite what you'd expect..."
- "The naming is misleading..."
- "This doesn't work the way the docs say..."
- Codebase quirks that caused confusion

**Integration Quirks:**

- "Gmail/Stripe/PostHog does X when you'd expect Y"
- API behaviors that caused issues
- Workarounds for external service limitations

**Process Learnings:**

- Workflow patterns that worked well
- Mistakes to avoid in future
- Testing strategies that caught bugs

### 3. Filter for Value

For each candidate insight, apply the test:

> "Would a naive agent, without our current context, benefit from knowing this?"

**Include if:**

- Codebase-specific (not generic programming knowledge)
- Non-obvious (can't be found by just reading the code)
- Actionable (tells you what to do or avoid)
- Durable (likely to still be true in 6 months)
- Strategic (architectural, not just tactical fixes)

**Exclude if:**

- Generic advice ("validate inputs", "handle errors")
- Temporary workaround that will be removed
- Already documented in CLAUDE.md or code comments
- Specific to this one PR/issue with no broader applicability
- Tactical CodeRabbit-style feedback (typos, formatting)

### 4. Check for Conflicts

Before presenting candidates, search for related existing learnings:

```bash
pnpm tsx scripts/knowledge-base.ts search --query "<candidate insight>" --threshold 0.5
```

If similar learnings exist, note them for user decision.

### 5. Present Candidates for Approval

Present learnings as a simple numbered list for user approval:

```markdown
## Candidate Learnings from [source]

1. **<Brief title>** - <One sentence description of the insight>

2. **<Brief title>** - <One sentence description of the insight>

3. **<Brief title>** - <One sentence description of the insight>

---

Which numbers do you want to capture? (all / 1,2,3 / none)
```

**Format rules:**

- One line per learning
- Bold title (3-6 words)
- Dash separator
- Single sentence description
- No metadata clutter (type, confidence, tags shown only after approval)

### 6. Store Approved Learnings

For each approved number, store using `/project:til` workflow.

After storing, report:

```text
Stored X learnings from this session.
```

## Example: Strategic vs Tactical

**Tactical (CodeRabbit-style) - Don't capture:**

> "Add type annotation to this variable"
> "Use const instead of let here"

**Strategic (Capture this!) - Do capture:**

> "We decided to use Redis for session storage because PostgreSQL was too slow for concurrent access patterns. The job queue was hitting 50+ concurrent reads/writes, causing lock contention."

> "The Thread model name is misleading - it's actually used for drafts only, not email threads. This has confused multiple agents. The name is legacy from when we planned to support threaded conversations."

## Script Commands Reference

```bash
# List recent conversation sessions
pnpm tsx scripts/conversation-history.ts list --recent 10

# Show only conversation summaries (fast, strategic)
pnpm tsx scripts/conversation-history.ts summaries --recent 5

# Extract full strategic content for AI analysis
pnpm tsx scripts/conversation-history.ts extract --strategic-only --recent 3

# Extract everything from a specific session
pnpm tsx scripts/conversation-history.ts extract --session <session-id>

# Filter by branch
pnpm tsx scripts/conversation-history.ts extract --branch feature/auth-system
```

## Conversation Patterns to Look For

| Pattern                       | Usually indicates          | Value     |
| ----------------------------- | -------------------------- | --------- |
| "The problem was..."          | Debugging insight          | High      |
| "It turns out..."             | Discovery moment           | High      |
| "We decided to..."            | Architectural decision     | Very High |
| "The reason we..."            | Rationale worth preserving | Very High |
| "Unlike what you'd expect..." | Non-obvious behavior       | High      |
| "The trick is..."             | Valuable technique         | Medium    |
| "We should always..."         | Pattern/practice           | Medium    |
| "Never do X because..."       | Gotcha/pitfall             | High      |

## Integration with BEADS

Extracted learnings are stored in `.beads/knowledge/` via the TIL command workflow:

- Conflict detection against existing facts
- Provenance tracking (source: "conversation", reference: session ID)
- Tagged by affected components

## What This Captures That TIL Doesn't

`/project:til` is for **explicit** insights you already recognize in the moment.

`/project:extract-learnings` mines for **implicit** insights buried in conversation:

- Historical sessions you've forgotten
- Decisions made weeks ago
- Patterns that emerged over multiple sessions
- Strategic context from conversation summaries

Both feed into the same knowledge base.
