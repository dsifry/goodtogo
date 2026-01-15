# Curate PR Learnings

Extract generalizable knowledge from CodeRabbit PR review comments using AI analysis.

## Usage

```
/project:curate-pr-learnings <pr-number>
```

## Architecture

This command follows the correct separation of concerns:

| Step | Component  | Type          | Operation                               |
| ---- | ---------- | ------------- | --------------------------------------- |
| 1    | Script     | Deterministic | Fetch PR comments from GitHub API       |
| 2    | Script     | Deterministic | Filter/format CodeRabbit comments       |
| 3    | **Claude** | **AI**        | **Analyze comments, extract learnings** |
| 4    | Script     | Deterministic | Validate learning structure             |
| 5    | Script     | Deterministic | Store in .beads/knowledge/\*.jsonl      |

**Scripts do NOT make AI calls.** AI analysis happens here in this command.

## Steps

### 1. Fetch PR Comments (Deterministic)

Run the fetch script to get raw PR data:

```bash
pnpm tsx scripts/curate-pr-learnings.ts fetch --pr $ARGUMENTS
```

This outputs JSON with:

- PR metadata (number, title, author, merge date)
- CodeRabbit comments (body, path, severity, category)

### 2. Analyze Comments (AI - Your Job)

For each CodeRabbit comment, use **extended thinking** to:

1. **Determine if it contains generalizable knowledge**
   - Does it describe a pattern that applies beyond this specific code?
   - Does it highlight a security, performance, or correctness concern?
   - Does it recommend a best practice?

2. **Extract the core insight**
   - What is the underlying principle?
   - Strip away the specific variable names, line numbers, file paths
   - Generalize to the pattern level

3. **Classify the learning**
   - Type: security | performance | api_behavior | code_quirk | pattern | gotcha | decision | dependency
   - Confidence: high | medium | low
   - Tags: relevant technologies, patterns, domains

4. **Formulate actionable recommendation**
   - What should developers do differently?
   - When does this apply?

### 3. Format Learnings

For each extracted learning, format as:

```json
{
  "type": "security|performance|api_behavior|code_quirk|pattern|gotcha|decision|dependency",
  "fact": "The generalized insight (no specific file/line references)",
  "recommendation": "What to do about it",
  "confidence": "high|medium|low",
  "tags": ["tag1", "tag2"],
  "affectedFiles": ["general/path/pattern/"],
  "provenance": {
    "source": "coderabbit",
    "reference": "PR #<number>",
    "date": "<ISO date>",
    "author": "coderabbitai[bot]",
    "context": "<first 500 chars of original comment>"
  }
}
```

### 4. Store Learnings (Deterministic)

Pass each learning to the store script:

```bash
pnpm tsx scripts/curate-pr-learnings.ts store --learning '<json>'
```

The script will:

- Validate the learning matches the schema
- Check for duplicates
- Append to .beads/knowledge/facts.jsonl

### 5. Present Candidates for Approval

Present learnings as a simple numbered list for user approval:

```
## Candidate Learnings from PR #<number>

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

**After user selects**, store the approved learnings and report:

```
Stored X learnings from PR #<number>.
```

## Example Analysis

**Original CodeRabbit comment:**

```
Instead of using `any` here, prefer explicit typing with `Record<string, unknown>`
for better type safety. This prevents accidental property access on undefined keys.
```

**AI Analysis (your job):**

```json
{
  "type": "pattern",
  "fact": "Using 'any' type bypasses TypeScript's type checking and can lead to runtime errors from undefined property access",
  "recommendation": "Use Record<string, unknown> or define explicit interfaces instead of 'any' to maintain type safety",
  "confidence": "high",
  "tags": ["typescript", "type-safety", "best-practice"],
  "affectedFiles": ["src/"],
  "provenance": {
    "source": "coderabbit",
    "reference": "PR #892",
    "date": "2026-01-10T00:00:00Z",
    "author": "coderabbitai[bot]",
    "context": "Instead of using `any` here, prefer explicit typing..."
  }
}
```

## What NOT To Do

- Do NOT use regex to extract insights (that's what AI is for)
- Do NOT have scripts make AI calls
- Do NOT store comments without AI analysis
- Do NOT skip the validation step

## When to Use

- After PR merge (triggered by PR Shepherd Phase 7)
- Manual curation of historical PRs
- Batch processing of recent PRs

## Related

- `scripts/curate-pr-learnings.ts` - Deterministic fetch/validate/store operations
- `.beads/knowledge/facts.jsonl` - Knowledge base storage
- PR Shepherd Phase 7 - Creates blocking task for curation
