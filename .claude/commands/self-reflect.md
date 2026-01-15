---
description: Extract learnings from recent PR reviews and update the knowledge base
---

# BEADS Self-Reflect

You are performing a weekly self-reflection for the BEADS agent swarm. Your job is to analyze PR review comments from the past week and extract high-quality, reusable learnings.

**Philosophy**: Be judicious. Quality over quantity. Each learning should make future development measurably better.

## Step 1: Fetch PR Comments

```bash
GITHUB_TOKEN=$(gh auth token) npx tsx scripts/beads-fetch-pr-comments.ts --days 7
```

This outputs PR comments to `.beads/temp/pr-comments.json`.

## Step 2: Extract CodeRabbit's Structured Learnings

CodeRabbit includes `🧠 Learnings used` and `✏️ Learnings added` sections with pre-canonicalized learnings. Extract them:

```bash
cat .beads/temp/pr-comments.json | jq -r '.comments[].body' | grep -A5 "^Learnt from:" | grep "^Learning:" | sed 's/^Learning: //' | sort -u
```

### Evaluate Each CodeRabbit Learning

**NOT all CodeRabbit learnings are equal.** Evaluate each one against these criteria:

#### ACCEPT (High Value)

- **Applies to patterns**: `Applies to **/*.test.ts: ...` - These are actionable file-scoped rules
- **NEVER/ALWAYS rules**: Clear, enforceable constraints
- **Security/Performance**: Critical quality gates
- **Gotchas with context**: Explains WHY something is problematic

#### REJECT or DEFER (Low Value)

- **PR-specific context**: "In PR #X, dsifry did Y" - Too specific unless the pattern generalizes
- **Personality observations**: "dsifry provides detailed updates" - Not actionable
- **Process descriptions**: "gdsveiga demonstrates pragmatic scope management" - Meta, not code
- **Duplicate with slight rewording**: Check if we already have this fact
- **Obvious/trivial**: Things any developer should know

#### TRANSFORM (Medium Value → Make High Value)

Some learnings need transformation to be useful:

- **Before**: "In PR #593, gdsveiga explains optional AIProvider methods support backward compatibility"
- **After**: "Optional interface methods (generateWithTools?, generateObject?) follow Interface Segregation Principle - add runtime guards before use"

### Quality Filter Questions

For each potential learning, ask:

1. **Would this prevent a bug?** If yes, high priority.
2. **Would this save review cycles?** If yes, add it.
3. **Is this codebase-specific or universal?** Tag accordingly.
4. **Do we already have this?** Check for semantic duplicates.
5. **Can an agent act on this?** If not actionable, skip it.

## Step 3: Analyze Comment Patterns

Beyond CodeRabbit's structured learnings, look for **recurring patterns** in review comments:

```bash
# Find comments mentioning common issues
cat .beads/temp/pr-comments.json | jq -r '.comments[] | select(.reviewerType == "coderabbit") | .body' | grep -i "nitpick\|issue\|suggestion\|consider\|should\|must\|avoid" | head -50
```

### Pattern Detection Checklist

Look for these patterns across multiple PRs:

1. **Repeated corrections**: Same issue flagged in multiple PRs → Create a learning
2. **Architectural feedback**: Comments about service design, dependencies → Capture the principle
3. **Testing feedback**: Mock patterns, test structure issues → Document the pattern
4. **Type safety issues**: Repeated type casting problems → Create a gotcha
5. **Performance concerns**: N+1 queries, memory issues → Document with context

### Example Pattern Analysis

If you see comments like:

- PR #801: "Consider using mock factories instead of manual mocks"
- PR #815: "Use createMockUser() from mock-factories.ts"
- PR #833: "Manual mock data should use factory pattern"

**Extract the pattern**:

```
fact: "Use mock factories from src/lib/services/mock-factories.ts instead of manually creating test data"
type: "pattern"
tags: ["testing", "mocking"]
affectedFiles: ["**/*.test.ts"]
```

## Step 4: Categorize and Store

For each validated learning:

```typescript
import { getKnowledgeCaptureService } from "@/lib/services/beads/knowledge-capture.service";

const service = getKnowledgeCaptureService();
await service.addFact({
  type: determineType(learning), // See type guide below
  fact: canonicalize(learning), // See canonicalization rules
  recommendation: extractAction(learning),
  confidence: assessConfidence(learning),
  provenance: [{ source, reference, date, context }],
  tags: extractTags(learning),
  affectedFiles: extractFilePatterns(learning),
});
```

### Type Guide

| Type           | When to Use                  | Example                                                 |
| -------------- | ---------------------------- | ------------------------------------------------------- |
| `pattern`      | Reusable code patterns       | "Use mock factories for test data"                      |
| `gotcha`       | Common mistakes/pitfalls     | "Truthy check fails for explicit zero values"           |
| `security`     | Security-sensitive patterns  | "Always validate JWT server-side"                       |
| `performance`  | Performance implications     | "Use database indexes for frequent queries"             |
| `decision`     | Team/architectural decisions | "Prefer Strategy over Template Method for AI providers" |
| `api_behavior` | External API quirks          | "Prisma findMany returns [] not null"                   |
| `code_quirk`   | Codebase-specific oddities   | "Thread model is for drafts only, not email threads"    |

### Canonicalization Rules

Transform raw learnings into actionable facts:

1. **Remove PR references**: "In PR #593..." → Remove, keep the principle
2. **Remove names when not relevant**: "dsifry prefers..." → Keep only if it's a team decision
3. **Generalize file paths**: `src/lib/services/foo.ts` → `src/lib/services/**/*.ts`
4. **Use imperative mood**: "Consider using..." → "Use..."
5. **Include the WHY**: "Use X" → "Use X because Y"
6. **Keep under 200 chars** when possible

### Confidence Assessment

| Level    | Criteria                                                                       |
| -------- | ------------------------------------------------------------------------------ |
| `high`   | Explicit rules (NEVER/ALWAYS), security issues, repeated pattern across 3+ PRs |
| `medium` | Single PR observation, team preference, architectural guidance                 |
| `low`    | Speculative, context-dependent, might not always apply                         |

## Step 5: Deduplication Check

Before adding, check for semantic duplicates:

```typescript
const existing = await service.search({ query: newFact.fact });
// Review matches - if >80% similar, skip or merge
```

## Step 6: Generate Report

```markdown
## Self-Reflection Results

### Summary

- PRs Analyzed: X
- Comments Reviewed: Y
- CodeRabbit Learnings Evaluated: Z
  - Accepted: A
  - Rejected (low value): B
  - Transformed: C
- Pattern-Based Learnings: W
- Total New Facts Added: N

### Learnings Added

#### High-Value CodeRabbit Learnings

1. **[pattern]** Applies to \*_/_.test.ts: Use mock factories...
   - Why accepted: Actionable, file-scoped, prevents test maintenance issues

#### Pattern-Detected Learnings

1. **[gotcha]** Truthy checks fail for explicit zero values
   - Detected in: PR #878, #865, #841
   - Pattern: Multiple type coercion issues

#### Rejected/Deferred

1. "In PR #593, gdsveiga explains..." - Too PR-specific, personality observation
2. "dsifry provides detailed updates" - Process observation, not actionable

### Knowledge Base Statistics

- Total facts: N
- By type: pattern (X), decision (Y), gotcha (Z)...
- Quality: high (A), medium (B), low (C)
```

## Quick Reference

```bash
# Full workflow
GITHUB_TOKEN=$(gh auth token) npx tsx scripts/beads-fetch-pr-comments.ts --days 7

# Extract CodeRabbit learnings for evaluation
cat .beads/temp/pr-comments.json | jq -r '.comments[].body' | \
  grep -A5 "^Learnt from:" | grep "^Learning:" | \
  sed 's/^Learning: //' | sort -u

# Find high-signal patterns
cat .beads/temp/pr-comments.json | jq -r \
  '.comments[] | select(.reviewerType == "coderabbit") |
   select(.body | test("nitpick|issue|must|never|always"; "i")) |
   "\(.prNumber): \(.body[0:200])"'

# Check for repeated issues across PRs
cat .beads/temp/pr-comments.json | jq -r '.comments[].body' | \
  grep -oE "(mock|type|test|service|pattern)" | sort | uniq -c | sort -rn

# Generate report
npx tsx scripts/beads-self-reflect.ts --no-slack
```

## Anti-Patterns to Avoid

1. **Quantity over quality**: Don't add 100 mediocre facts; add 10 great ones
2. **Blindly trusting CodeRabbit**: Evaluate each learning critically
3. **Ignoring duplicates**: Check before adding
4. **Missing the WHY**: Facts without reasoning are less useful
5. **Over-specificity**: "Use X in file Y" → "Use X in files matching pattern"
6. **Under-specificity**: "Write good tests" → Not actionable, skip it
