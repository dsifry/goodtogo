---
description: Extract learnings from recent PR reviews and update the knowledge base
---

# Self-Reflect

Analyze PR review comments from the past week and extract high-quality, reusable learnings.

**Philosophy**: Be judicious. Quality over quantity. Each learning should make future development measurably better.

## Step 1: Fetch PR Comments

Use the GitHub CLI to fetch merged PRs from the past week and their review comments:

```bash
# Calculate date 7 days ago (works on macOS and Linux)
SINCE=$(date -v-7d +%Y-%m-%d 2>/dev/null || date -d '7 days ago' +%Y-%m-%d)

# List PRs merged in the past week
gh pr list --state merged --search "merged:>=$SINCE" --limit 20 --json number,title,mergedAt

# For each PR merged in the past week, fetch review comments
for pr in $(gh pr list --state merged --search "merged:>=$SINCE" --limit 20 --json number -q '.[].number'); do
  echo "=== PR #$pr ==="
  gh api repos/{owner}/{repo}/pulls/$pr/comments --jq '.[] | "[\(.user.login)] \(.body[0:300])"' 2>/dev/null | head -10
  gh api repos/{owner}/{repo}/pulls/$pr/reviews --jq '.[] | select(.body != "") | "[\(.user.login)] \(.body[0:500])"' 2>/dev/null | head -5
done
```

## Step 2: Extract CodeRabbit's Structured Learnings

CodeRabbit includes `🧠 Learnings used` and `✏️ Learnings added` sections. Look for these in review comments.

### Evaluate Each Learning

**NOT all learnings are equal.** Evaluate each one against these criteria:

#### ACCEPT (High Value)

- **Applies to patterns**: `Applies to **/*.test.*: ...` - Actionable file-scoped rules
- **NEVER/ALWAYS rules**: Clear, enforceable constraints
- **Security/Performance**: Critical quality gates
- **Gotchas with context**: Explains WHY something is problematic

#### REJECT or DEFER (Low Value)

- **PR-specific context**: "In PR #X, user did Y" - Too specific unless pattern generalizes
- **Personality observations**: "User provides detailed updates" - Not actionable
- **Process descriptions**: Meta observations, not code-related
- **Duplicate with slight rewording**: Check existing facts first
- **Obvious/trivial**: Things any developer should know

#### TRANSFORM (Medium Value → Make High Value)

Some learnings need transformation:

- **Before**: "In PR #593, the optional methods support backward compatibility"
- **After**: "Optional interface methods follow Interface Segregation Principle - add runtime guards before use"

### Quality Filter Questions

1. **Would this prevent a bug?** If yes, high priority.
2. **Would this save review cycles?** If yes, add it.
3. **Is this codebase-specific or universal?** Tag accordingly.
4. **Do we already have this?** Check for semantic duplicates.
5. **Can an agent act on this?** If not actionable, skip it.

## Step 3: Analyze Comment Patterns

Look for **recurring patterns** across multiple PRs:

1. **Repeated corrections**: Same issue flagged in multiple PRs → Create a learning
2. **Architectural feedback**: Comments about design, dependencies → Capture the principle
3. **Testing feedback**: Test patterns, structure issues → Document the pattern
4. **Type safety issues**: Repeated type problems → Create a gotcha
5. **Performance concerns**: N+1 queries, memory issues → Document with context

## Step 4: Store Learnings

Add validated learnings to `.beads/knowledge/facts.json`:

```json
{
  "id": "unique-id",
  "type": "pattern|gotcha|security|performance|decision|api_behavior|code_quirk",
  "fact": "The learning in imperative mood",
  "recommendation": "What to do about it",
  "confidence": "high|medium|low",
  "tags": ["relevant", "tags"],
  "affectedFiles": ["**/*.py"],
  "provenance": {
    "source": "pr-review|debugging|conversation",
    "reference": "PR #N or description",
    "date": "YYYY-MM-DD",
    "reviewer": "who identified this"
  }
}
```

### Type Guide

| Type           | When to Use                  | Example                                        |
| -------------- | ---------------------------- | ---------------------------------------------- |
| `pattern`      | Reusable code patterns       | "Use mock factories for test data"             |
| `gotcha`       | Common mistakes/pitfalls     | "Truthy check fails for explicit zero values"  |
| `security`     | Security-sensitive patterns  | "Always validate tokens server-side"           |
| `performance`  | Performance implications     | "Use database indexes for frequent queries"    |
| `decision`     | Team/architectural decisions | "Prefer composition over inheritance"          |
| `api_behavior` | External API quirks          | "GitHub API returns workflow names, not jobs"  |
| `code_quirk`   | Codebase-specific oddities   | "Thread model is for drafts only"              |

### Canonicalization Rules

1. **Remove PR references**: "In PR #593..." → Remove, keep the principle
2. **Remove names when not relevant**: "User prefers..." → Keep only if team decision
3. **Generalize file paths**: `src/foo/bar.py` → `src/foo/**/*.py`
4. **Use imperative mood**: "Consider using..." → "Use..."
5. **Include the WHY**: "Use X" → "Use X because Y"
6. **Keep under 200 chars** when possible

### Confidence Assessment

| Level    | Criteria                                                                       |
| -------- | ------------------------------------------------------------------------------ |
| `high`   | Explicit rules (NEVER/ALWAYS), security issues, repeated pattern across 3+ PRs |
| `medium` | Single PR observation, team preference, architectural guidance                 |
| `low`    | Speculative, context-dependent, might not always apply                         |

## Step 5: Check for Duplicates

Before adding, review existing facts in `.beads/knowledge/facts.json` for semantic duplicates. If similar exists, consider:

- **New supersedes old**: Update the existing fact
- **Keep both**: They capture different aspects
- **Merge**: Combine into one comprehensive fact
- **Discard new**: Existing fact is sufficient

## Step 6: Generate Report

```markdown
## Self-Reflection Results

### Summary

- PRs Analyzed: X
- Comments Reviewed: Y
- Learnings Evaluated: Z
  - Accepted: A
  - Rejected (low value): B
  - Transformed: C
- Total New Facts Added: N

### Learnings Added

1. **[type]** Brief description
   - Why accepted: Reason

### Rejected/Deferred

1. "Learning text" - Reason for rejection

### Knowledge Base Statistics

- Total facts: N
- By type: pattern (X), gotcha (Y), decision (Z)...
```

## Anti-Patterns to Avoid

1. **Quantity over quality**: Don't add 100 mediocre facts; add 10 great ones
2. **Blindly trusting reviewers**: Evaluate each learning critically
3. **Ignoring duplicates**: Check before adding
4. **Missing the WHY**: Facts without reasoning are less useful
5. **Over-specificity**: "Use X in file Y" → "Use X in files matching pattern"
6. **Under-specificity**: "Write good tests" → Not actionable, skip it

## Language-Agnostic Notes

This workflow works with any programming language:

- Uses `gh` CLI for GitHub operations (language-independent)
- Uses shell tools (`jq`, `grep`) for processing
- Stores learnings in JSON format
- File patterns use glob syntax that works across languages
