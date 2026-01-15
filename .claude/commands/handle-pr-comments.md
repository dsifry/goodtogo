# /project:handle-pr-comments

Handle review comments on pull requests with appropriate responses and resolutions.

## Usage

```
/project:handle-pr-comments <pr-number>
```

## Overview

This command helps systematically address PR review comments from automated tools (like CodeRabbit) and human reviewers. It ensures consistent, professional responses that acknowledge the AI assistance.

---

## 🚨 CRITICAL: Complete PR Lifecycle Protocol

**A PR is NOT complete until ALL of the following are true:**

1. ✅ All CI checks pass
2. ✅ **EVERY** code review comment has been addressed (including trivial/nitpicks)
3. ✅ **EVERY** comment thread has received an individual response
4. ✅ All threads are marked as resolved (after reviewer approval)
5. ✅ Any work > 1 day has a GitHub issue created
6. ✅ No pending reviewer comments awaiting response
7. ✅ ALL tests pass, there are no pre-existing issues or flaky tests - these are excuses. Fix the underlying issues, don't disable tests.
8. ✅ **No new reviews after last commit with actionable items** (Section 1d)

### Mandatory Comment Handling Rules

| Comment Type           | Action                     | DO NOT Skip                 |
| ---------------------- | -------------------------- | --------------------------- |
| 🔴 Critical/Major      | Fix immediately            | Never                       |
| 🟠 High/Medium         | Fix before merge           | Never                       |
| 🟡 Minor               | Fix                        | Never                       |
| 🔵 **Trivial/Nitpick** | **FIX THESE TOO**          | ❌ These matter!            |
| 🟣 **Out-of-scope**    | **INVESTIGATE THOROUGHLY** | ❌ Often the BEST insights! |
| 👤 Human comments      | Always address             | Never                       |

### Work Sizing Decision

For EACH comment:

- **< 1 day of work** → Implement the fix in this PR
- **> 1 day of work** OR architectural change → Create a new GitHub issue, link it in your response

### Iteration Loop

```text
REPEAT until (all_threads_resolved AND no_new_comments AND no_new_reviews_after_commit):
  1. Fetch ALL inline comments (including trivial, out-of-scope)
  1b. ⚠️ CHECK REVIEW BODIES for "Outside diff range" comments (Section 1c)
      - These are NOT threads - they're in the review body text
      - Commonly missed because they don't appear as threads!
  2. Check for NEW REVIEWS after last commit (Section 1d) ← CRITICAL!
  3. For each comment: fix OR create issue OR respond with disagreement
  4. Run validation: pnpm lint && pnpm typecheck && pnpm test --run
  5. Commit and push
  6. Respond to EVERY thread individually
  6b. For "Outside diff range" comments: leave a general PR comment acknowledging
  7. ⚠️ CRITICAL: WAIT FOR CI/CD, then RE-CHECK for NEW comments/reviews
     - Monitor CI/CD pipeline: `gh pr checks $PR_NUMBER --watch`
     - Wait until ALL checks complete (not just pass - complete)
     - Automated reviewers (CodeRabbit) post comments during/after their check
     - Check BOTH inline threads AND review bodies for new feedback
     - Check for NEW REVIEWS with "Actionable comments posted: X" (X > 0)
  8. If new comments OR new reviews exist → GO TO STEP 1
  9. If no new comments/reviews AND all checks complete → verify all threads resolved, then complete
```

**⚠️ THE #1 WORKFLOW FAILURE**: Stopping after responding without checking for new comments/reviews.
**⚠️ THE #2 WORKFLOW FAILURE**: Missing "Outside diff range" comments in review bodies.

Automated reviewers POST NEW COMMENTS after analyzing your fix commit. You MUST loop back.
"Outside diff range" comments are in REVIEW BODIES, not threads. You MUST check them (Section 1c).

**Thread Resolution Policy**:

- ✅ Resolve when: code committed + responded + reviewer acknowledged
- ✅ Resolve immediately if declining a suggestion (with explanation)
- ❌ Never auto-resolve without reviewer acknowledgment

---

## Cross-Platform Compatibility

**IMPORTANT**: This command is designed to work on both Windows (Git Bash) and Mac/Linux with automatic fallback logic.

**How it works**:

- **First choice**: Uses `jq` if available (more powerful, supports complex queries)
- **Fallback**: Uses `gh api -q` (GitHub CLI's built-in jq subset) for simpler queries
- Compatible with Windows Git Bash, Mac, and Linux
- No additional dependencies required beyond `gh` CLI (but `jq` is recommended for full functionality)

## Rate Limit Considerations

GitHub has separate rate limits for REST API and GraphQL API:

- **REST API**: 5,000 requests/hour with PAT
- **GraphQL API**: 5,000 points/hour with PAT (complex queries cost multiple points)

This command uses **REST API exclusively** to avoid GraphQL rate limit issues. If you encounter rate limits, check both:

```bash
# Check REST API rate limit
gh api rate_limit -q '.rate'

# Check GraphQL API rate limit (separate from REST)
gh api graphql -f query='{ rateLimit { limit remaining resetAt } }' -q '.data.rateLimit'
```

## Critical Workflow Notes

**⚠️ IMPORTANT**: Comment IDs can change after you push commits. Always:

1. Get initial comment IDs
2. Make your fixes and commit
3. **RE-FETCH comment IDs** before posting responses (comments may have been updated/replaced)
4. Post responses to CURRENT comment IDs (not stale ones from before your commit)
5. **WAIT for reviewer confirmation** - Do NOT resolve threads immediately after your reply
6. Only resolve threads when: (a) reviewer confirms they're satisfied, OR (b) you're explicitly declining/ignoring the suggestion

**Resolution Policy**:

- ✅ **Wait for reviewer approval** before resolving addressed feedback
- ✅ **Resolve immediately** only if declining a suggestion (explain why in your reply)
- ❌ **Never auto-resolve** after posting a fix - let the reviewer verify

**Pattern**: Use GraphQL for thread operations (variables via -f/-F; parse with `-q` on fetch or `jq` for stored JSON) and REST for posting replies.

## Workflow

### 1. Check for New Comments (Cross-Platform)

**Pattern**: Use GraphQL for thread operations (variables via -f/-F; parse with `-q` on fetch or `jq` for stored JSON) and REST for posting replies.

```bash
# === VALIDATION: Ensure required tools and context ===
echo "=== VALIDATING ENVIRONMENT ==="

# Check gh CLI is installed
if ! command -v gh &> /dev/null; then
  echo "❌ ERROR: GitHub CLI (gh) not installed or not in PATH"
  echo "Install from: https://cli.github.com/"
  exit 1
fi

# Verify authentication
if ! gh auth status &> /dev/null; then
  echo "❌ ERROR: Not authenticated with GitHub CLI"
  echo "Run: gh auth login"
  exit 1
fi

# Test repo access
if ! gh repo view &> /dev/null; then
  echo "❌ ERROR: Not in a git repository or no GitHub remote configured"
  echo "Navigate to your repository directory first"
  exit 1
fi

echo "✓ GitHub CLI installed and authenticated"
echo ""

# Check for jq and set appropriate JSON parser
if command -v jq &> /dev/null; then
  USE_JQ=true
  echo "✓ jq found - using full jq functionality"
else
  USE_JQ=false
  echo "⚠️  jq not found - using gh api -q fallback (limited functionality)"
fi
echo ""

# Set PR number variable to avoid repetition and reduce errors
# IMPORTANT: Replace XXX with your actual PR number
PR_NUMBER=XXX

# Validate PR_NUMBER (must be positive integer)
if [ -z "$PR_NUMBER" ] || [ "$PR_NUMBER" = "XXX" ] || ! [[ "$PR_NUMBER" =~ ^[1-9][0-9]*$ ]]; then
  echo "❌ ERROR: Invalid PR_NUMBER='$PR_NUMBER'"
  echo "Usage: Set PR_NUMBER to a valid pull request number (e.g., PR_NUMBER=512)"
  echo "PR numbers must be positive integers (1, 2, 3, ...)"
  echo "HINT: Replace 'PR_NUMBER=XXX' with your actual PR number like 'PR_NUMBER=512'"
  exit 1
fi

# Get repo owner and name
OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)

# Verify PR exists
if ! gh pr view "$PR_NUMBER" &> /dev/null; then
  echo "❌ ERROR: PR #$PR_NUMBER not found in $OWNER/$REPO_NAME"
  echo "Check the PR number and try again"
  exit 1
fi

echo "✓ Validation passed"
echo ""
echo "Repository: $OWNER/$REPO_NAME"
echo "PR Number: $PR_NUMBER"

# === STEP 1: COUNT COMMENTS (using gh api -q) ===
echo ""
echo "=== COMMENT COUNTS ==="
ISSUE_COUNT=$(gh api "repos/$OWNER/$REPO_NAME/issues/$PR_NUMBER/comments" --paginate -q 'length')
REVIEW_COUNT=$(gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate -q 'length')
echo "Issue comments (general PR comments): $ISSUE_COUNT"
echo "Review comments (inline code comments): $REVIEW_COUNT"

# === STEP 2: LIST ALL REVIEW COMMENTS WITH DETAILS ===
echo ""
echo "=== REVIEW COMMENTS ==="

# Use temp file approach (eval-safe for all shells and platforms)
# Note: /tmp/ works on Mac/Linux/Windows Git Bash (mapped to Windows temp dir)
TEMP_COMMENTS="/tmp/pr_${PR_NUMBER}_comments_$$.json"

# Write API output to temp file with error handling
if ! gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate > "$TEMP_COMMENTS" 2>/dev/null; then
  echo "❌ ERROR: Failed to write to $TEMP_COMMENTS"
  echo "Check disk space: df -h /tmp"
  echo "Check permissions: ls -ld /tmp"
  exit 1
fi

if [ "$USE_JQ" = true ]; then
  # Use jq for full functionality (supports string slicing)
  jq -r '.[] | "ID: \(.id) - [\(.path):\(.line // .original_line // "?")]", "  @\(.user.login): \(.body[0:100])...", "  URL: https://github.com/'"$OWNER"'/'"$REPO_NAME"'/pull/'"$PR_NUMBER"'#discussion_r\(.id)", "---"' < "$TEMP_COMMENTS"
else
  # Fallback: basic text extraction without jq
  grep -o '"id":[0-9]*' "$TEMP_COMMENTS" | cut -d: -f2 | while read -r id; do
    echo "Comment ID: $id"
    echo "  (Use: gh api repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments --paginate -q '.[] | select(.id == $id)')"
    echo "---"
  done
fi

rm -f "$TEMP_COMMENTS"

# === STEP 2b: GET REVIEW THREAD IDs (for resolution tracking) ===
echo ""
echo "=== REVIEW THREADS (with resolution status) ==="

# Pagination support: Fetch ALL review threads (handles PRs with >50 threads)
CURSOR=""
HAS_NEXT=true

while [ "$HAS_NEXT" = "true" ]; do
  # Build GraphQL query using variables (secure approach)
  if [ -z "$CURSOR" ]; then
    # First page - no cursor needed
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                isResolved
                comments(first: 1) {
                  nodes {
                    databaseId
                    path
                    author { login }
                  }
                }
              }
            }
          }
        }
      }')
  else
    # Subsequent pages - include cursor
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f cursor="$CURSOR" \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!, $cursor: String!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50, after: $cursor) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                isResolved
                comments(first: 1) {
                  nodes {
                    databaseId
                    path
                    author { login }
                  }
                }
              }
            }
          }
        }
      }')
  fi

  # Extract and display threads from this page
  # Note: body field omitted to avoid control character issues in GraphQL responses
  if [ "$USE_JQ" = true ]; then
    # Use jq for full functionality (can parse piped JSON)
    echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] |
      "Thread: \(.id)",
      "  Resolved: \(.isResolved)",
      "  Comment ID: \(.comments.nodes[0].databaseId)",
      "  File: \(.comments.nodes[0].path)",
      "  Author: @\(.comments.nodes[0].author.login)",
      "---"'
  else
    # Fallback: No jq - show warning about pagination limitation
    if [ -z "$CURSOR" ]; then
      echo "⚠️  jq not found - showing first 50 threads only (pagination disabled)"
    fi
    # Extract basic info without jq (limited output)
    echo "$RESPONSE" | grep -o '"databaseId":[0-9]*' | head -1 | cut -d: -f2 | while read -r dbId; do
      echo "Thread data requires jq for full display"
      echo "  Comment ID: $dbId"
      echo "  (Install jq for full thread information)"
      echo "---"
    done
  fi

  # Check if there are more pages
  if [ "$USE_JQ" = true ]; then
    HAS_NEXT=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  else
    # Without jq, stop pagination after first page
    HAS_NEXT="false"
  fi

  # Get next cursor
  if [ "$HAS_NEXT" = "true" ]; then
    if [ "$USE_JQ" = true ]; then
      CURSOR=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
      echo "=== Fetching next page of threads... ==="
    fi
  fi
done

# === STEP 3: GET SPECIFIC COMMENT DETAILS (when needed) ===
# Only run this after identifying which comments need responses
# Replace COMMENT_ID with actual ID from step 2
# COMMENT_ID=2470790976
# gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
#   -q ".[] | select(.id == $COMMENT_ID)"

# === OPTIONAL: Filter for specific user (e.g., CodeRabbit) ===
# echo ""
# echo "=== CODERABBIT COMMENTS ==="
# gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
#   -q '.[] | select(.user.login | contains("coderabbit")) | "[\(.path):\(.line)] \(.body[0:100])..."'
```

### 1b. Filter Actionable vs Non-Actionable Comments

**CRITICAL**: Before processing comments, filter out non-actionable ones to avoid wasting time on confirmations and acknowledgments.

```bash
# Run the filter script
bin/pr-comments-filter.sh $PR_NUMBER
```

This script:

- Filters out non-actionable comments (confirmations, acknowledgments, fingerprinting)
- Categorizes actionable comments by priority (🔴 Critical → 🔵 Low)
- Shows comment IDs and details for processing

**Priority levels:**

| Priority        | Marker                                                   | Action           |
| --------------- | -------------------------------------------------------- | ---------------- |
| 🔴 **CRITICAL** | `_⚠️ Potential issue_ \| _🔴 Critical_`                  | Fix immediately  |
| 🟠 **HIGH**     | `_⚠️ Potential issue_ \| _🟠 Major_`                     | Fix before merge |
| 🟡 **MEDIUM**   | `_🟡 Minor_` or `_🛠️ Refactor suggestion_ \| _🟠 Major_` | Fix              |
| 🔵 **LOW**      | `_🔵 Trivial_` / `_🧹 Nitpick_`                          | **Fix** ⚠️       |
| 👤 **HUMAN**    | Non-bot comments                                         | Always process   |

> **⚠️ Note**: ALL comment types require fixes. See [Complete PR Lifecycle Protocol](#-critical-complete-pr-lifecycle-protocol) - trivial/nitpicks are NOT optional.

### 1c. Extract "Outside Diff Range" Comments from Review Bodies (CRITICAL)

**⚠️ COMMONLY MISSED**: CodeRabbit posts "Outside diff range" comments in the **review body**, not as inline threads. These are actionable feedback that MUST be addressed.

```bash
# Extract Outside diff range comments from review bodies
PR_NUMBER=XXX  # Replace with your PR number
OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)

echo "=== OUTSIDE DIFF RANGE COMMENTS (from review bodies) ==="
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/reviews" --paginate | \
  jq -r '.[] | select(.body | test("Outside diff range"; "i")) |
    "Review ID: \(.id)\nAuthor: \(.user.login)\n\n\(.body)\n\n---"'
```

**What to look for in the output**:

- `<summary>⚠️ Outside diff range comments (N)</summary>` sections
- File paths and line numbers referenced
- Specific actionable feedback (not just "run validation")

**These comments are NOT in threads** - they cannot be replied to inline. You must:

1. Address the feedback in your code
2. Commit and push
3. Leave a general PR comment acknowledging you addressed them

### 1d. Identify Other Out-of-Scope Comments

**Out-of-scope comments** are review comments that fall outside the PR's changed lines.

```bash
# Run the out-of-scope detection script
bin/pr-comments-out-of-scope.sh $PR_NUMBER
```

This script detects comments using 5 methods:

1. **REST API**: `line == null` with `original_line` set (outdated position)
2. **REST API**: `position == null` (completely outdated)
3. **GraphQL**: `isOutdated` flag (MOST RELIABLE)
4. **CodeRabbit**: "Outside diff range" in review body (see Section 1c above)
5. **Issue comments**: General PR discussion with actionable feedback

**IMPORTANT**: Treat out-of-scope comments as **IN SCOPE** by default. Reviewers took time to provide feedback - address it.

#### Handling Out-of-Scope Comments

For each out-of-scope comment, use **ultrathink** to evaluate:

```text
ultrathink: Analyze this out-of-scope review comment:
- What is the reviewer asking for?
- How complex is this change? (lines of code, files affected)
- Does it require refactoring other systems?
- Can I complete this in under 30 minutes?
- Are there any risks or dependencies?

Recommend: FIX_NOW or CREATE_ISSUE
```

**Decision Matrix** (aligned with [Work Sizing Decision](#work-sizing-decision)):

| Criteria                                | Action           |
| --------------------------------------- | ---------------- |
| < 1 day of work, straightforward fix    | **FIX_NOW**      |
| > 1 day of work OR architectural change | **CREATE_ISSUE** |
| Truly unclear (can't estimate)          | **ASK_USER**     |

> **Default action**: FIX_NOW. Out-of-scope comments often contain the most valuable insights - treat them as IN SCOPE unless clearly > 1 day of work.

### 1d. Check for New Reviews After Commit (CRITICAL)

**🚨 WHY THIS MATTERS**: CodeRabbit and other review bots post **review summaries** that indicate actionable comments. These are separate from inline comments and threads. If you only check threads, you'll miss new reviews posted after your commit.

**Example of what we missed**: Review 3647101676 posted "Actionable comments posted: 1" with fix instructions - but we weren't checking reviews, only threads.

```bash
# === CHECK FOR NEW REVIEWS AFTER YOUR COMMIT ===
# This catches CodeRabbit's "Actionable comments posted: X" summaries

# Get the latest commit timestamp on the PR
LATEST_SHA=$(gh pr view $PR_NUMBER --json headRefOid -q .headRefOid)
COMMIT_TIME=$(gh api "repos/$OWNER/$REPO_NAME/commits/$LATEST_SHA" -q .commit.committer.date)
echo "Latest commit: $LATEST_SHA at $COMMIT_TIME"

# Fetch all reviews and filter for those after the commit
echo ""
echo "=== REVIEWS AFTER LAST COMMIT ==="

gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/reviews" --paginate > /tmp/pr_${PR_NUMBER}_reviews_$$.json

python3 << PYEOF
import json
from datetime import datetime

commit_time = datetime.fromisoformat("$COMMIT_TIME".replace('Z', '+00:00'))

with open('/tmp/pr_${PR_NUMBER}_reviews_$$.json') as f:
    reviews = json.load(f)

new_reviews = []
for review in reviews:
    submitted = datetime.fromisoformat(review['submitted_at'].replace('Z', '+00:00'))
    if submitted > commit_time:
        new_reviews.append({
            'id': review['id'],
            'author': review['user']['login'],
            'state': review['state'],
            'submitted': review['submitted_at'],
            'body': review['body'][:200] if review['body'] else ''
        })

if new_reviews:
    print(f"⚠️  Found {len(new_reviews)} review(s) after last commit:")
    for r in new_reviews:
        print(f"\n  Review ID: {r['id']}")
        print(f"  Author: @{r['author']}")
        print(f"  State: {r['state']}")
        print(f"  Submitted: {r['submitted']}")
        if 'Actionable comments posted:' in r['body']:
            print(f"  🚨 CONTAINS ACTIONABLE COMMENTS!")
        print(f"  Body: {r['body'][:150]}...")
else:
    print("✅ No new reviews after last commit")
PYEOF

rm -f /tmp/pr_${PR_NUMBER}_reviews_$$.json
```

**What to look for**:

| Review Content                          | Action Required                                     |
| --------------------------------------- | --------------------------------------------------- |
| "Actionable comments posted: 0"         | No action needed                                    |
| "Actionable comments posted: X" (X > 0) | **NEW COMMENTS TO ADDRESS** - check inline comments |
| "Fix all issues with AI agents" section | Contains specific fix instructions                  |
| Human reviewer comments                 | Always address                                      |

**Integration with workflow**: After checking threads (Section 1), ALWAYS run this review check. If new reviews with actionable comments exist, you must:

1. Find the corresponding inline comments
2. Address them
3. Commit and push
4. Re-run this check (restart the cycle)

#### Creating GitHub Issues for Complex Out-of-Scope Items

```bash
# Create a GitHub issue for deferred work
PR_NUMBER=XXX  # Set your PR number
ISSUE_TITLE="Refactor: <brief description>"
REVIEWER_COMMENT="<paste the reviewer's comment here>"
SUGGESTED_APPROACH="<your analysis>"
FILES_AFFECTED="- file1.ts\n- file2.ts"

gh issue create \
  --title "$ISSUE_TITLE" \
  --body "## Context

This was identified during review of PR #$PR_NUMBER.

## Reviewer Comment

> $REVIEWER_COMMENT

## Suggested Approach

$SUGGESTED_APPROACH

## Files Affected

$FILES_AFFECTED

---
*Created from PR review feedback*"

# Note the issue number from the output, then reply to the PR comment
ISSUE_NUMBER=<new-issue-number>
COMMENT_ID=<original-comment-id>
CURRENT_USER=$(gh api user -q '.login')

gh api "/repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies" \
  -X POST \
  -f body="Created issue #$ISSUE_NUMBER to track this. The suggested change requires broader refactoring that's outside the scope of this PR, but it's a good improvement to make.

*(Response by Claude on behalf of @$CURRENT_USER)*"
```

### 2. Map Comment IDs to Thread IDs

Create a mapping between comment IDs and thread IDs for easy reference:

**Prerequisites**: This section requires variables from Section 1 (`$OWNER`, `$REPO_NAME`, `$PR_NUMBER`, `$USE_JQ`). Either run Section 1 first, or define these variables manually:

```bash
# Define these if not running Section 1 first
# OWNER=$(gh repo view --json owner -q .owner.login)
# REPO_NAME=$(gh repo view --json name -q .name)
# PR_NUMBER=512  # Replace with your PR number
# USE_JQ=true    # Set based on whether jq is installed
```

```bash
# Save comment-to-thread mapping to temp file
# Supports pagination for PRs with >50 review threads

# Use PID-based unique filename to prevent race conditions
TEMP_FILE="/tmp/pr_thread_mapping_${PR_NUMBER}_$$.txt"

# Clear the mapping file and check for write errors
if ! > "$TEMP_FILE" 2>/dev/null; then
  echo "❌ ERROR: Cannot create temp file $TEMP_FILE"
  echo "Check disk space: df -h /tmp"
  echo "Check permissions: ls -ld /tmp"
  exit 1
fi

# Option 1: Using gh api -q with pagination (cross-platform, no jq required)
CURSOR=""
HAS_NEXT=true

while [ "$HAS_NEXT" = "true" ]; do
  # Build GraphQL query using variables (secure approach)
  if [ -z "$CURSOR" ]; then
    # First page - no cursor needed
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                isResolved
                comments(first: 1) {
                  nodes {
                    databaseId
                    path
                  }
                }
              }
            }
          }
        }
      }')
  else
    # Subsequent pages - include cursor
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f cursor="$CURSOR" \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!, $cursor: String!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50, after: $cursor) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                isResolved
                comments(first: 1) {
                  nodes {
                    databaseId
                    path
                  }
                }
              }
            }
          }
        }
      }')
  fi

  # Append threads from this page to mapping file (with error handling)
  if [ "$USE_JQ" = true ]; then
    # Use jq for full functionality
    if ! echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] |
      "\(.comments.nodes[0].databaseId):\(.id):\(.isResolved):\(.comments.nodes[0].path)"' >> "$TEMP_FILE" 2>/dev/null; then
      echo "❌ ERROR: Failed to write to $TEMP_FILE"
      echo "Disk may be full. Check: df -h /tmp"
      rm -f "$TEMP_FILE"  # Cleanup on failure
      exit 1
    fi
  else
    # Fallback: Extract basic info without jq
    if [ -z "$CURSOR" ]; then
      echo "⚠️  jq not found - mapping will have limited information (pagination disabled)"
    fi
    # Extract comment IDs only (limited mapping without thread IDs)
    echo "$RESPONSE" | grep -o '"databaseId":[0-9]*' | cut -d: -f2 | while read -r dbId; do
      echo "$dbId:(requires jq):(requires jq):(requires jq)" >> "$TEMP_FILE"
    done
  fi

  # Check if there are more pages
  if [ "$USE_JQ" = true ]; then
    HAS_NEXT=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  else
    # Without jq, stop pagination after first page
    HAS_NEXT="false"
  fi

  # Get next cursor
  if [ "$HAS_NEXT" = "true" ]; then
    if [ "$USE_JQ" = true ]; then
      CURSOR=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
    fi
  fi
done

# Option 2: Using jq with pagination (if you have jq installed)
# # Same TEMP_FILE variable as Option 1 above
# CURSOR=""
# HAS_NEXT=true
#
# while [ "$HAS_NEXT" = "true" ]; do
#   # Use direct string interpolation (same as Option 1)
#   if [ -z "$CURSOR" ]; then
#     AFTER_CLAUSE=""
#   else
#     AFTER_CLAUSE=", after: \"$CURSOR\""
#   fi
#
#   RESPONSE=$(gh api graphql -f query="{
#     repository(owner: \"$OWNER\", name: \"$REPO_NAME\") {
#       pullRequest(number: $PR_NUMBER) {
#         reviewThreads(first: 50$AFTER_CLAUSE) {
#           pageInfo {
#             hasNextPage
#             endCursor
#           }
#           nodes {
#             id
#             isResolved
#             comments(first: 1) {
#               nodes {
#                 databaseId
#                 path
#               }
#             }
#           }
#         }
#       }
#     }
#   }")
#
#   if ! echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] |
#     "\(.comments.nodes[0].databaseId):\(.id):\(.isResolved):\(.comments.nodes[0].path)"' >> "$TEMP_FILE" 2>/dev/null; then
#     echo "❌ ERROR: Failed to write to $TEMP_FILE"
#     rm -f "$TEMP_FILE"
#     exit 1
#   fi
#
#   HAS_NEXT=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
#
#   # Get next cursor
#   if [ "$HAS_NEXT" = "true" ]; then
#     CURSOR=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
#   fi
# done

echo "=== COMMENT → THREAD MAPPING (ALL PAGES) ==="
echo "Format: CommentID:ThreadID:Resolved:FilePath"
cat "$TEMP_FILE"
```

**Usage**: When you respond to comment ID 2519563186, you can look up its thread ID and resolution status from this mapping.

### 2b. Determine Current User and PR Author

```bash
# Get the current GitHub user
CURRENT_USER=$(gh api user -q '.login')
echo "Current user: @$CURRENT_USER"

# Get PR details including author
PR_AUTHOR=$(gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER" -q '.user.login')
echo "PR authored by: @$PR_AUTHOR"

# Verify authorization
if [ "$CURRENT_USER" != "$PR_AUTHOR" ]; then
  echo "WARNING: You (@$CURRENT_USER) are not the PR author (@$PR_AUTHOR)"
  echo "Only respond to comments if you have explicit permission to act on behalf of @$PR_AUTHOR"
fi
```

### 3. Resolving Review Threads

After successfully addressing a review comment, you can mark the thread as resolved programmatically.

#### 3a. Resolve a Single Thread

```bash
# Set the thread ID from step 2b
THREAD_ID="PRRT_kwDOK-xA485huO-2"  # Example thread ID

# Resolve the thread using GraphQL variables
gh api graphql \
  -f threadId="$THREAD_ID" \
  -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread {
        id
        isResolved
      }
    }
  }'

# Verify resolution using GraphQL variables
gh api graphql \
  -f nodeId="$THREAD_ID" \
  -f query='
  query($nodeId: ID!) {
    node(id: $nodeId) {
      ... on PullRequestReviewThread {
        id
        isResolved
      }
    }
  }'
```

#### 3b. Unresolve a Thread (if needed)

```bash
# Unresolve a thread (useful if accidentally resolved or need to reopen discussion)
gh api graphql \
  -f threadId="$THREAD_ID" \
  -f query='
  mutation($threadId: ID!) {
    unresolveReviewThread(input: {threadId: $threadId}) {
      thread {
        id
        isResolved
      }
    }
  }'
```

#### 3c. Batch Resolve Multiple Threads

```bash
# Example: Resolve multiple threads after addressing all comments
for THREAD_ID in "PRRT_kwDOK-xA485huO-2" "PRRT_kwDOK-xA486abc123" "PRRT_kwDOK-xA487xyz789"; do
  echo "Resolving thread: $THREAD_ID"
  gh api graphql \
    -f threadId="$THREAD_ID" \
    -f query='
    mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread { id isResolved }
      }
    }
  '
  echo ""
done
```

#### 3d. Check Resolution Status for All Threads

```bash
# List all unresolved threads with pagination support
echo "=== UNRESOLVED THREADS (ALL PAGES) ==="

# Option 1: Using gh api -q with pagination (cross-platform, no jq required)
CURSOR=""
HAS_NEXT=true

while [ "$HAS_NEXT" = "true" ]; do
  # Build GraphQL query using variables (secure approach)
  if [ -z "$CURSOR" ]; then
    # First page - no cursor needed
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                isResolved
                comments(first: 1) {
                  nodes {
                    databaseId
                    path
                    author { login }
                  }
                }
              }
            }
          }
        }
      }')
  else
    # Subsequent pages - include cursor
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f cursor="$CURSOR" \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!, $cursor: String!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50, after: $cursor) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                isResolved
                comments(first: 1) {
                  nodes {
                    databaseId
                    path
                    author { login }
                  }
                }
              }
            }
          }
        }
      }')
  fi

  # Display unresolved threads from this page
  # Note: body field omitted to avoid control character issues in GraphQL responses
  if [ "$USE_JQ" = true ]; then
    # Use jq for full functionality
    echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] |
      select(.isResolved == false) |
      "Thread: \(.id)",
      "  Comment ID: \(.comments.nodes[0].databaseId)",
      "  File: \(.comments.nodes[0].path)",
      "  Author: @\(.comments.nodes[0].author.login)",
      "---"'
  else
    # Fallback: Basic extraction without jq
    if [ -z "$CURSOR" ]; then
      echo "⚠️  jq not found - showing limited thread information (pagination disabled)"
    fi
    echo "$RESPONSE" | grep -o '"databaseId":[0-9]*' | head -1 | cut -d: -f2 | while read -r dbId; do
      echo "Unresolved thread (requires jq for full info)"
      echo "  Comment ID: $dbId"
      echo "---"
    done
  fi

  # Check if there are more pages
  if [ "$USE_JQ" = true ]; then
    HAS_NEXT=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  else
    # Without jq, stop pagination after first page
    HAS_NEXT="false"
  fi

  # Get next cursor
  if [ "$HAS_NEXT" = "true" ]; then
    if [ "$USE_JQ" = true ]; then
      CURSOR=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
      echo "=== Fetching next page of threads... ==="
    fi
  fi
done
```

**Important Notes on Thread Resolution**:

- Thread IDs have format `PRRT_kwDOK-xA485huO-2` (not the same as comment IDs)
- Use Section 1, STEP 2b or Section 2 to get thread IDs alongside comment IDs
- **Wait for reviewer confirmation** before resolving - don't auto-resolve after posting your fix
- Only resolve immediately if you're **declining** the suggestion (explain why)
- Resolving threads is visible to all PR participants
- You can always unresolve if discussion needs to continue

### 4. Posting Inline Replies (Technical Implementation)

**⚠️ CRITICAL WORKFLOW ORDER**:

1. **BEFORE making fixes**: Get initial comment IDs and thread information
2. **Make your fixes**: Code changes, commit, push
3. **⚠️ REFRESH comment IDs**: Re-fetch CURRENT comments (IDs may have changed after your commit!)
4. **Post responses**: Use CURRENT comment IDs to post replies
5. **WAIT for reviewer**: Do NOT resolve threads - let reviewer verify your fix
6. **Resolve only when**: Reviewer approves OR you're declining the suggestion

**Why refresh matters**: When you push commits that address review comments, GitHub may:

- Update comment context (line numbers change)
- Create new comment IDs for the same thread
- Mark old comment IDs as stale (causing 404 errors)

**Correct API Pattern**: Use GitHub REST API for posting comment replies:

```bash
# STEP 1: Get CURRENT comment IDs after making your fixes
# IMPORTANT: Replace XXX with your actual PR number
PR_NUMBER=XXX
OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)
CURRENT_USER=$(gh api user -q .login)

echo "=== CURRENT REVIEW COMMENTS (after your fixes) ==="
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
  -q '.[] | "ID: \(.id) | Path: \(.path):\(.line) | @\(.user.login): \(.body[0:80])..."'

# STEP 2: Post replies to CURRENT comment IDs
# Note: Use actual numeric IDs from above output
COMMENT_ID=<current-comment-id>  # Use FRESH ID from step 1

gh api "/repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies" \
  -X POST \
  -f body="Fixed in commit <commit-hash>.

*(Response by Claude on behalf of @$CURRENT_USER)*"
```

**Key Points**:

- ✅ Use `/pulls/{pr_number}/comments/{comment_id}/replies` endpoint (NOT `/pulls/comments/{id}/replies`)
- ✅ Use POST method (`-X POST`)
- ✅ Include attribution in every response body
- ✅ **ALWAYS refresh comment IDs after pushing commits**
- ❌ Don't use comment IDs from before your commit (will get 404 errors)

**Example - Responding to Multiple Comments (Complete Workflow)**:

```bash
# Get repo info
OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)
CURRENT_USER=$(gh api user -q .login)
PR_NUMBER=512

# STEP 1: Make your fixes (commit and push)
git add .
git commit -m "fix: address review feedback"
git push

# STEP 2: ⚠️ REFRESH - Get CURRENT comment IDs (after push)
echo "=== Getting CURRENT comment IDs after push ==="
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
  -q '.[] | "\(.id) - \(.path):\(.line // .original_line) - @\(.user.login)"'

# STEP 3: Post replies to CURRENT comment IDs from step 2 output
# Replace these with ACTUAL IDs from the output above
for COMMENT_ID in 2519755966 2519755970 2519755975; do
  echo "Responding to comment $COMMENT_ID..."
  gh api "/repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies" \
    -X POST \
    -f body="Fixed in commit $(git rev-parse --short HEAD).

*(Response by Claude on behalf of @$CURRENT_USER)*" \
    && echo "✓ Response posted" \
    || echo "✗ Failed (comment may be stale - refresh IDs)"
done
```

**Troubleshooting 404 Errors**:
If you get `404 Not Found` when posting replies:

1. ✅ **Most likely cause**: Comment ID is stale (from before your commit)
2. ✅ **Solution**: Re-run the comment ID fetch command (step 2 above)
3. ✅ **Use FRESH IDs**: Replace your comment IDs with newly fetched ones
4. ✅ **Verify**: Check the comment still exists on GitHub web UI

**Troubleshooting 422 Validation Errors**:
If you get `422 Validation Failed` with error "commit_id is not part of the pull request":

1. ✅ **Cause**: You included `-f commit_id="<hash>"` parameter when posting a reply
2. ✅ **Solution**: **Remove the `-f commit_id` parameter entirely**
3. ✅ **Why**: When posting replies with `-F in_reply_to=<id>`, the commit context is inherited from the parent comment
4. ✅ **Note**: The `commit_id` parameter is only for creating NEW review comments on specific lines, not for replies

### 5. Response Templates

**Important**: All comments must include attribution: `*(Response by Claude on behalf of @$CURRENT_USER)*`
**Note**: If you're not the PR author, ensure you have permission to respond on their behalf.
**Use extended thinking (ultrathink) to analyze each comment and decide whether to accept or reject it, then:**

#### Simple Fixes (typos, formatting)

**Workflow**:

1. Make the change
2. Commit and push
3. **Refresh comment IDs** (see Section 4)
4. Post reply using CURRENT comment ID
5. **Wait for reviewer approval** before resolving
6. _(Only resolve immediately if declining the suggestion)_

```bash
# STEP 1: Make fix, commit, push
git add . && git commit -m "fix: typo" && git push

# STEP 2: Get CURRENT comment IDs after push
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
  -q '.[] | "\(.id) - \(.path):\(.line)"'

# STEP 3: Post reply to CURRENT comment ID (from step 2)
COMMENT_ID=<fresh-comment-id>  # Use ID from step 2
gh api "/repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies" \
  -X POST \
  -f body="Fixed in commit $(git rev-parse --short HEAD). 👍

*(Response by Claude on behalf of @$CURRENT_USER)*"

echo "✓ Reply posted. Waiting for reviewer approval before resolving."
echo ""
echo "⏸️  STOPPING HERE - Do not proceed to resolution yet"
echo ""
echo "📝 Next steps:"
echo "   1. Wait for reviewer to verify your fix"
echo "   2. When reviewer approves, use Section 4a for resolution"
echo "   3. OR if declining suggestion, use Section 4b for immediate resolution"
echo ""

# ==================== STOP HERE ====================
# Only proceed to Section 4a or 4b when:
# ✓ Reviewer has explicitly approved your fix, OR
# ✓ You are declining the suggestion (must explain why in reply)
# ==================================================
```

#### 4a. Resolution After Reviewer Approval

##### ⚠️ ONLY run this AFTER reviewer confirms they're satisfied with your fix

```bash
# Get thread ID for approved comment
COMMENT_ID=<comment-id-from-approved-fix>  # Comment ID that was approved
OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)
PR_NUMBER=<pr-number>  # IMPORTANT: Set this to your PR number (e.g., PR_NUMBER=512)

# Set USE_JQ if not already defined (required for thread lookup)
# If you've run Section 1, this is already set. Otherwise, define it here:
if [ -z "$USE_JQ" ]; then
  USE_JQ=$(command -v jq >/dev/null 2>&1 && echo "true" || echo "false")
fi

# Get thread ID for this comment (search through all pages if needed)
THREAD_ID=""
CURSOR=""
HAS_NEXT=true

while [ "$HAS_NEXT" = "true" ] && [ -z "$THREAD_ID" ]; do
  # Build GraphQL query using variables (secure approach)
  if [ -z "$CURSOR" ]; then
    # First page - no cursor needed
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                comments(first: 10) {
                  nodes { databaseId }
                }
              }
            }
          }
        }
      }')
  else
    # Subsequent pages - include cursor
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f cursor="$CURSOR" \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!, $cursor: String!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50, after: $cursor) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                comments(first: 10) {
                  nodes { databaseId }
                }
              }
            }
          }
        }
      }')
  fi

  # Try to find matching thread in this page (checks all comments in thread, not just first)
  if [ "$USE_JQ" = true ]; then
    # Use jq for full functionality - searches across all comments in each thread
    THREAD_ID=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] |
      select(any(.comments.nodes[]; .databaseId == '"$COMMENT_ID"')) | .id')
  else
    # Without jq, cannot reliably search through GraphQL results
    echo "❌ ERROR: jq is required for thread ID lookup"
    echo "Install jq or use Section 2 to manually find thread ID"
    exit 1
  fi

  if [ -n "$THREAD_ID" ]; then
    break  # Found it!
  fi

  # Check if there are more pages
  if [ "$USE_JQ" = true ]; then
    HAS_NEXT=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  else
    HAS_NEXT="false"
  fi

  # Get next cursor
  if [ "$HAS_NEXT" = "true" ]; then
    if [ "$USE_JQ" = true ]; then
      CURSOR=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
    fi
  fi
done

if [ -z "$THREAD_ID" ]; then
  echo "Error: Could not find thread for comment $COMMENT_ID"
  exit 1
fi

# Resolve the thread using direct string interpolation
echo "Resolving thread $THREAD_ID..."
gh api graphql \
  -f threadId="$THREAD_ID" \
  -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread { id isResolved }
    }
  }' && echo "✓ Thread resolved" || echo "✗ Resolution failed"
```

#### 4b. Resolution When Declining Suggestion

##### Use this ONLY when you're explicitly declining/ignoring a reviewer's suggestion

```bash
# IMPORTANT: Your reply MUST explain why you're declining the suggestion
# Example: "Not implementing alphabetization here because the current order groups..."

# Get thread ID for the declined suggestion
COMMENT_ID=<comment-id-of-declined-suggestion>
OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)
PR_NUMBER=<pr-number>  # IMPORTANT: Set this to your PR number (e.g., PR_NUMBER=512)

# Find and resolve thread immediately (since you've declined the suggestion)
# [Use same thread lookup code as Section 4a]

echo "✓ Thread resolved (suggestion declined with explanation)"
```

#### Substantive Changes

**Workflow**:

1. Implement the suggestion
2. Commit and push
3. **Refresh comment IDs** (critical!)
4. Post detailed reply using CURRENT comment ID
5. **Wait for reviewer approval** - let them verify the fix works
6. _(Only resolve immediately if declining the suggestion)_

```bash
# STEP 1: Implement fix, commit, push
git add . && git commit -m "fix: add type definitions" && git push

# STEP 2: Get CURRENT comment IDs
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
  -q '.[] | "\(.id) - \(.path):\(.line)"'

# STEP 3: Post reply with CURRENT comment ID
COMMENT_ID=<fresh-comment-id>  # Use ID from step 2
COMMIT_HASH=$(git rev-parse --short HEAD)

gh api "/repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies" \
  -X POST \
  -f body="Fixed in commit $COMMIT_HASH - Added proper type definitions for the EmailService interface instead of using 'any'. This provides better type safety and intellisense support throughout the codebase.

*(Response by Claude on behalf of @$CURRENT_USER)*"

echo "✓ Reply posted. Waiting for reviewer approval before resolving."
echo ""
echo "⏸️  STOPPING HERE - Do not proceed to resolution yet"
echo ""
echo "📝 Next steps:"
echo "   1. Wait for reviewer to verify your fix"
echo "   2. When reviewer approves, use Section 4a for resolution"
echo "   3. OR if declining suggestion, use Section 4b for immediate resolution"
echo ""

# ==================== STOP HERE ====================
# Only proceed to Section 4a or 4b when:
# ✓ Reviewer has explicitly approved your fix, OR
# ✓ You are declining the suggestion (must explain why in reply)
# ==================================================
```

#### Alternative: Bulk Resolve Without Individual Replies

**⚠️ IMPORTANT**: This should ONLY be used when the reviewer has given explicit approval to bulk resolve, or when you've discussed the approach with them first.

**When to use**: When you've made comprehensive fixes addressing multiple comments in a single commit, posting individual replies would be redundant, **AND the reviewer has approved this approach**.

**Workflow**:

1. Make all fixes in one commit with descriptive message
2. Push the commit
3. **Get reviewer confirmation** that bulk resolution is acceptable
4. Bulk resolve all addressed threads

```bash
# STEP 0: AUTHORIZATION CHECK (Required for bulk resolution)
echo "=== AUTHORIZATION CHECK ==="
echo "⚠️  Bulk resolution should ONLY be used by the PR author after reviewer approval"
echo ""

# Get PR author and current user
OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)
# IMPORTANT: Replace XXX with your actual PR number
PR_NUMBER=XXX

# Verify PR exists and get PR author
PR_AUTHOR=$(gh pr view "$PR_NUMBER" --json author -q .author.login 2>/dev/null)
if [ -z "$PR_AUTHOR" ]; then
  echo "❌ ERROR: PR #$PR_NUMBER not found"
  exit 1
fi

# Get current authenticated user
CURRENT_USER=$(gh api user -q .login)

# Check if current user is the PR author
if [ "$CURRENT_USER" != "$PR_AUTHOR" ]; then
  echo "❌ ERROR: Authorization failed"
  echo "   PR author: @$PR_AUTHOR"
  echo "   Current user: @$CURRENT_USER"
  echo ""
  echo "Only the PR author can bulk resolve threads."
  echo "If you're helping with someone else's PR, post individual replies instead."
  exit 1
fi

echo "✓ Authorized: You are the PR author (@$PR_AUTHOR)"
echo ""

# Manual confirmation prompt
echo "⚠️  WARNING: You are about to bulk resolve threads on PR #$PR_NUMBER"
echo ""
echo "This should ONLY be done when:"
echo "  1. Reviewer has explicitly approved bulk resolution"
echo "  2. All fixes are comprehensive and self-explanatory"
echo "  3. Commit message clearly describes all changes"
echo ""
read -p "Have you received reviewer approval for bulk resolution? (yes/no): " CONFIRMATION

if [ "$CONFIRMATION" != "yes" ]; then
  echo ""
  echo "❌ Bulk resolution cancelled"
  echo "Please use individual replies (Sections 4a/4b) and wait for reviewer approval instead."
  exit 0
fi

echo "✓ Confirmation received. Proceeding with bulk resolution..."
echo ""

# STEP 1: Make comprehensive fixes
git add . && git commit -m "fix: address all review feedback

- Replace | jq -r with gh api -q for cross-platform compatibility
- Add both gh api -q and commented jq options
- Clarify section references
- All three locations updated" && git push

# STEP 2: Get all unresolved thread IDs with pagination support

echo "=== UNRESOLVED THREADS (ALL PAGES) ==="
CURSOR=""
HAS_NEXT=true
UNRESOLVED_THREADS=()

while [ "$HAS_NEXT" = "true" ]; do
  # Build GraphQL query using variables (secure approach)
  if [ -z "$CURSOR" ]; then
    # First page - no cursor needed
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                isResolved
                comments(first: 1) {
                  nodes {
                    databaseId
                    author { login }
                  }
                }
              }
            }
          }
        }
      }')
  else
    # Subsequent pages - include cursor
    RESPONSE=$(gh api graphql \
      -f owner="$OWNER" \
      -f repoName="$REPO_NAME" \
      -F prNumber=$PR_NUMBER \
      -f cursor="$CURSOR" \
      -f query='query($owner: String!, $repoName: String!, $prNumber: Int!, $cursor: String!) {
        repository(owner: $owner, name: $repoName) {
          pullRequest(number: $prNumber) {
            reviewThreads(first: 50, after: $cursor) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                isResolved
                comments(first: 1) {
                  nodes {
                    databaseId
                    author { login }
                  }
                }
              }
            }
          }
        }
      }')
  fi

  # Display unresolved threads (for user visibility)
  if [ "$USE_JQ" = true ]; then
    # Use jq for full functionality (supports string slicing)
    echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] |
      select(.isResolved == false) |
      "Thread: \(.id)",
      "  Comment: \(.comments.nodes[0].databaseId)",
      "  Author: @\(.comments.nodes[0].author.login)",
      "---"'
  else
    # Fallback: Without jq, cannot do bulk operations
    echo "❌ ERROR: Bulk resolution requires jq for safe operation"
    echo "Install jq or resolve threads individually using Section 4a"
    exit 1
  fi

  # Collect ONLY thread IDs into array
  if [ "$USE_JQ" = true ]; then
    while IFS= read -r thread_id; do
      UNRESOLVED_THREADS+=("$thread_id")
    done < <(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.nodes[] |
      select(.isResolved == false) | .id')
  fi

  # Check if there are more pages
  if [ "$USE_JQ" = true ]; then
    HAS_NEXT=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage')
  else
    HAS_NEXT="false"
  fi

  # Get next cursor
  if [ "$HAS_NEXT" = "true" ]; then
    if [ "$USE_JQ" = true ]; then
      CURSOR=$(echo "$RESPONSE" | jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor')
      echo "=== Fetching next page of threads... ==="
    fi
  fi
done

# STEP 3: Resolve each thread that your commit addressed
# Option 1: Resolve specific threads manually (replace with actual thread IDs)
for THREAD_ID in PRRT_kwDOK-xA485huprE PRRT_kwDOK-xA485huprJ PRRT_kwDOK-xA485huprO; do
  echo "Resolving thread $THREAD_ID..."
  gh api graphql \
    -f threadId="$THREAD_ID" \
    -f query='
    mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread { id isResolved }
      }
    }' && echo "✓ Resolved" || echo "✗ Failed"
done

# Option 2: Resolve ALL unresolved threads (use with caution!)
# Uncomment if you've addressed ALL review feedback:
# for THREAD_ID in "${UNRESOLVED_THREADS[@]}"; do
#   [[ "$THREAD_ID" =~ ^PRRT_ ]] || continue  # Skip non-thread-ID lines
#   echo "Resolving thread $THREAD_ID..."
#   gh api graphql \
#     -f threadId="$THREAD_ID" \
#     -f query='
#     mutation($threadId: ID!) {
#       resolveReviewThread(input: {threadId: $threadId}) {
#         thread { id isResolved }
#       }
#     }' && echo "✓ Resolved" || echo "✗ Failed"
# done
```

**When NOT to use**:

- ❌ When reviewer hasn't approved bulk resolution approach
- ❌ When comments require individual explanations
- ❌ When rejecting suggestions (must provide reasoning)
- ❌ When you only addressed some comments (be selective)
- ❌ When you haven't discussed this approach with the reviewer

**Best practice**:

1. **Default approach**: Post individual replies and wait for reviewer approval
2. **Bulk resolution**: Only use after getting reviewer's explicit approval for this approach
3. Use bulk resolution for simple fixes where the commit message is self-explanatory

#### Rejecting Suggestions

- Reply with reasoning:

  ```
  Not implementing alphabetization here because the current order groups related commands by functionality (onboarding, testing, PR management). This makes it easier for users to discover related commands.

  *(Response by Claude on behalf of @$CURRENT_USER)*
  ```

- Mark as resolved only if explanation is clear

#### Need Clarification

- Reply:

  ```
  I'm not sure I understand this suggestion. Could you clarify what you mean by [specific part]? Are you suggesting [interpretation A] or [interpretation B]?

  *(Response by Claude on behalf of @$CURRENT_USER)*
  ```

- **DO NOT mark as resolved** - leave open for response

#### Partial Implementation

- Reply:

  ```
  Partially implemented in commit xyz789 - I've added the type safety checks as suggested, but held off on the refactoring portion as it would affect 15+ files. Should we tackle that in a separate PR?

  *(Response by Claude on behalf of @$CURRENT_USER)*
  ```

- **DO NOT mark as resolved** - needs team decision

### 4.1. Example Responses

**Type Safety Fix**:

```
Updated in commit 4773c13 - Replaced the `any` type with a proper `UserPreferences` interface that matches the API response structure. This ensures type safety throughout the preference handling code.

*(Response by Claude on behalf of @$CURRENT_USER)*
```

**Performance Improvement**:

```
Implemented in commit 89abc12 - Added React.memo() to the ExpensiveComponent and moved the calculation into a useMemo hook. This prevents unnecessary re-renders when parent state changes.

*(Response by Claude on behalf of @$CURRENT_USER)*
```

**Security Concern**:

```
Good catch! Fixed in commit def456 - Sanitized the user input using DOMPurify before rendering to prevent XSS attacks. Also added input validation at the API level.

*(Response by Claude on behalf of @$CURRENT_USER)*
```

### 5. Best Practices

1. **Be Thorough**: Address **ALL** comments - including trivial/nitpicks and out-of-scope
2. **Be Complete**: Address all parts of multi-part suggestions (don't cherry-pick)
3. **Be Iterative**: Follow the [Iteration Loop](#iteration-loop) - don't declare complete until ALL threads resolved
4. **Be Responsive**: Reply to **EVERY** comment thread individually (not batch responses)
5. **Be Specific**: Reference exact commits, files, and line numbers
6. **Be Professional**: Thank reviewers for catching important issues
7. **Be Transparent**: Always include the Claude attribution
8. **Be Humble**: Acknowledge when you need help or clarification
9. **Create Issues**: For work > 1 day, create a GitHub issue instead of deferring indefinitely

### 6. Post-Push Verification (MANDATORY)

**⚠️ CRITICAL**: After EVERY push, you MUST check for NEW comments before declaring complete.

```bash
# STEP 1: Wait for ALL CI/CD checks to complete (not just pass - complete)
PR_NUMBER=XXX  # Replace with your PR number
echo "⏳ Waiting for CI/CD checks to complete..."
gh pr checks $PR_NUMBER --watch

# STEP 2: Set up environment
OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)
CURRENT_USER=$(gh api user -q .login)

# Check for jq availability
if command -v jq &> /dev/null; then
  USE_JQ=true
else
  USE_JQ=false
  echo "⚠️ jq not found - using gh api -q fallback (limited functionality)"
fi

echo "=== CHECKING FOR NEW COMMENTS ==="

# Get the timestamp of your most recent reply
LAST_REPLY_TIME=$(gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
  -q "[.[] | select(.user.login == \"$CURRENT_USER\") | select(.in_reply_to_id)] | sort_by(.created_at) | last | .created_at")

# Handle case where user has no previous replies
if [ -z "$LAST_REPLY_TIME" ] || [ "$LAST_REPLY_TIME" = "null" ]; then
  echo "⚠️ No previous replies found - checking all comments as new"
  LAST_REPLY_TIME="1970-01-01T00:00:00Z"  # Unix epoch - treat all comments as new
else
  echo "Your last reply was at: $LAST_REPLY_TIME"
fi

# STEP 3: Find NEW inline comments posted AFTER your last reply
if [ "$USE_JQ" = true ]; then
  NEW_INLINE=$(gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate | \
    jq -r --arg time "$LAST_REPLY_TIME" '[.[] | select(.in_reply_to_id == null) | select(.created_at > $time)] | length')

  if [ "$NEW_INLINE" -gt 0 ]; then
    echo ""
    echo "🚨 $NEW_INLINE NEW INLINE COMMENT(S) DETECTED"
    gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate | \
      jq -r --arg time "$LAST_REPLY_TIME" '.[] | select(.in_reply_to_id == null) | select(.created_at > $time) | "⚠️ NEW: ID \(.id) by @\(.user.login) at \(.created_at)\n   File: \(.path):\(.line)\n   Body: \(.body[0:80])...\n---"'
  fi
else
  # Fallback: count new comments using gh api -q (limited - no time comparison)
  echo "⚠️ Using fallback method - please manually verify no new comments since $LAST_REPLY_TIME"
  NEW_INLINE=0  # Cannot determine without jq
fi

# STEP 4: Check review bodies for new "Outside diff range" comments
if [ "$USE_JQ" = true ]; then
  NEW_REVIEWS=$(gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/reviews" --paginate | \
    jq -r --arg time "$LAST_REPLY_TIME" '[.[] | select(.submitted_at > $time) | select(.body | test("Outside diff range"; "i"))] | length')

  if [ "$NEW_REVIEWS" -gt 0 ]; then
    echo ""
    echo "🚨 $NEW_REVIEWS NEW REVIEW BODY COMMENT(S) WITH 'Outside diff range' DETECTED"
    gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/reviews" --paginate | \
      jq -r --arg time "$LAST_REPLY_TIME" '.[] | select(.submitted_at > $time) | select(.body | test("Outside diff range"; "i")) | "Review ID: \(.id) by @\(.user.login)\n---"'
  fi
else
  NEW_REVIEWS=0  # Cannot determine without jq
fi

# STEP 5: Summary
TOTAL_NEW=$((NEW_INLINE + NEW_REVIEWS))

if [ "$TOTAL_NEW" -gt 0 ]; then
  echo ""
  echo "🚨 TOTAL NEW COMMENTS: $NEW_INLINE inline + $NEW_REVIEWS review body = $TOTAL_NEW"
  echo "ACTION REQUIRED: Address these new comments and iterate again."
  echo "DO NOT DECLARE COMPLETE"
else
  echo ""
  echo "✅ No new comments since your last reply."
fi
```

**If new comments are found**: Go back to Step 1 of the Iteration Loop. DO NOT proceed to completion.

### 7. Verify All Comments Have Been Responded To

**CRITICAL**: Before declaring the task complete, verify EVERY comment has a response.

**Pattern**: Use `gh api -q` for cross-platform compatibility without external `jq`.

```bash
# === STEP 1: Get current user (for filtering responses) ===
CURRENT_USER=$(gh api user -q '.login')
echo "=== Verification for user: @$CURRENT_USER ==="

# === STEP 2: List all original review comments (not replies) ===
echo ""
echo "=== ALL REVIEW COMMENTS (should all have responses) ==="
gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
  -q '.[] | select(.in_reply_to_id == null) | .id, .user.login, .path, (.line // .original_line)' | \
  while read -r id; read -r user; read -r path; read -r line; do
    echo "[ ] ID: $id - $path:$line - @$user"
    echo "    URL: https://github.com/$OWNER/$REPO_NAME/pull/$PR_NUMBER#discussion_r$id"
  done

# === STEP 3: List your responses ===
echo ""
echo "=== YOUR RESPONSES ==="

if [ "$USE_JQ" = true ]; then
  # Use jq for full functionality (supports string slicing)
  gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate | \
    jq -r '.[] | select(.user.login == "'"$CURRENT_USER"'") | select(.in_reply_to_id) | "✓ Replied to ID \(.in_reply_to_id): \(.body[0:80])..."'
else
  # Fallback to gh api -q (no string slicing, show reply count only)
  gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
    -q '.[] | select(.user.login == "'"$CURRENT_USER"'") | select(.in_reply_to_id) | "✓ Replied to ID \(.in_reply_to_id)"'
fi

# === STEP 4: Find comments without responses (cross-platform method) ===
echo ""
echo "=== CHECKING FOR UNREPLIED COMMENTS ==="

# Use PID-based unique filenames to prevent race conditions
ORIGINAL_IDS_FILE="/tmp/pr_original_ids_${PR_NUMBER}_$$.txt"
REPLIED_IDS_FILE="/tmp/pr_replied_ids_${PR_NUMBER}_$$.txt"

# Get list of original comment IDs directly from API (with error handling)
if ! gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
  -q '.[] | select(.in_reply_to_id == null) | .id' > "$ORIGINAL_IDS_FILE" 2>/dev/null; then
  echo "❌ ERROR: Failed to write to $ORIGINAL_IDS_FILE"
  echo "Check disk space: df -h /tmp"
  rm -f "$ORIGINAL_IDS_FILE" "$REPLIED_IDS_FILE"  # Cleanup on failure
  exit 1
fi

# Get list of comment IDs you replied to directly from API (with error handling)
if ! gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
  -q ".[] | select(.user.login == \"$CURRENT_USER\") | select(.in_reply_to_id) | .in_reply_to_id" > "$REPLIED_IDS_FILE" 2>/dev/null; then
  echo "❌ ERROR: Failed to write to $REPLIED_IDS_FILE"
  echo "Check disk space: df -h /tmp"
  rm -f "$ORIGINAL_IDS_FILE" "$REPLIED_IDS_FILE"  # Cleanup on failure
  exit 1
fi

# Find unreplied comments
UNREPLIED_COUNT=0
while read -r COMMENT_ID; do
  if ! grep -q "^${COMMENT_ID}$" "$REPLIED_IDS_FILE" 2>/dev/null; then
    gh api "repos/$OWNER/$REPO_NAME/pulls/$PR_NUMBER/comments" --paginate \
      -q ".[] | select(.id == $COMMENT_ID) | \"⚠️  NO RESPONSE: ID \(.id) - \(.path):\(.line) by @\(.user.login)\""
    UNREPLIED_COUNT=$((UNREPLIED_COUNT + 1))
  fi
done < "$ORIGINAL_IDS_FILE"

# === STEP 5: Summary ===
echo ""
echo "=== VERIFICATION SUMMARY ==="
ORIGINAL_COUNT=$(wc -l < "$ORIGINAL_IDS_FILE" | tr -d ' ')
REPLIED_COUNT=$(wc -l < "$REPLIED_IDS_FILE" | tr -d ' ')
echo "Original comments: $ORIGINAL_COUNT"
echo "Your responses: $REPLIED_COUNT"

if [ "$UNREPLIED_COUNT" -eq 0 ]; then
  echo ""
  echo "✅ SUCCESS: All $ORIGINAL_COUNT comments have been responded to!"
else
  echo ""
  echo "❌ INCOMPLETE: $UNREPLIED_COUNT comment(s) still need responses"
fi
```

**Note on Verification Approach**:

- The verification step uses temp files only to store filtered ID lists for shell-based comparison logic
- All JSON parsing is done via direct API calls with `gh api -q` (piped inline, not from temp files)
- This eliminates the need for standalone `jq` while maintaining cross-platform compatibility

**Checklist Before Completing Task** (see [Complete PR Lifecycle Protocol](#-critical-complete-pr-lifecycle-protocol)):

- [ ] **ALL comments addressed** - including trivial/nitpicks and out-of-scope
- [ ] **EVERY thread has individual response** - no batch responses
- [ ] **⚠️ POST-PUSH VERIFICATION**: Ran Section 6 to check for NEW comments after push
- [ ] **No new comments found** after waiting 60+ seconds post-push
- [ ] Ran the comment listing command (Section 7)
- [ ] Verified each comment has a response
- [ ] Confirmed no "NO RESPONSE" warnings in summary
- [ ] All responses include proper attribution: `*(Response by Claude on behalf of @username)*`
- [ ] **Checked for new REVIEWS after last commit** (Section 1d) - no "Actionable comments posted: X" (X > 0)
- [ ] **Waited for next review cycle** - not auto-resolving
- [ ] **All threads resolved** (after reviewer approval)
- [ ] **GitHub issues created** for any work > 1 day
- [ ] Cleaned up temp files (see Section 8)

**⚠️ The task is NOT complete until ALL boxes are checked, ALL threads are resolved, AND no new reviews with actionable items exist.**
**⚠️ THE #1 FAILURE MODE: Not checking for new comments/reviews after push. Always run Section 6.**

### 8. Cleanup Temp Files

**IMPORTANT**: Always clean up temp files after completing the PR comment workflow.

```bash
# Remove all temp files created during this workflow
# Uses PID-based pattern to catch files from this PR number
rm -f /tmp/pr_original_ids_${PR_NUMBER}_*.txt \
      /tmp/pr_replied_ids_${PR_NUMBER}_*.txt \
      /tmp/pr_thread_mapping_${PR_NUMBER}_*.txt \
      /tmp/pr_${PR_NUMBER}_comments_*.json

echo "✓ Temp files cleaned up"
```

**When to clean up**:

- After successfully responding to all comments
- After verifying all responses
- Before switching to a different PR or task
- If you need to start over with fresh data

### 9. When to Use This Command

- After pushing commits to an existing PR
- Before switching away from a PR branch
- When specifically asked to check PR comments
- After completing significant work on a PR
- **After each review cycle** - iterate until all threads resolved

**Note**: Only handle comments on PRs you authored unless explicitly asked otherwise.

### 10. When is the PR Truly Complete?

A PR is **NOT ready for merge** until:

1. ✅ All CI checks pass
2. ✅ **EVERY** comment (including trivial/nitpicks/out-of-scope) has been addressed
3. ✅ **EVERY** thread has an individual response
4. ✅ All threads are marked resolved (after reviewer approval)
5. ✅ GitHub issues created for any deferred work (> 1 day)
6. ✅ No pending reviewer comments awaiting response
7. ✅ **No new reviews after last commit with actionable items** (check Section 1d)

**If ANY of these are false, continue iterating.** Do not declare complete prematurely.

**Common failure mode**: Declaring complete after resolving threads, but missing a new review posted AFTER the commit that contains "Actionable comments posted: 1". Always run Section 1d check before declaring complete.

## Troubleshooting

### "jq: command not found" error

If you see this error, it means the command uses standalone `jq` instead of `gh api -q`. This version of the command has been updated to avoid this issue by using only `gh api -q` for JSON parsing.

### Windows-specific issues

- **Temp files**: Uses `/tmp/` which works on Git Bash (MSYS)
- **Command syntax**: All commands tested on Windows Git Bash
- **Line endings**: Git Bash handles Unix-style line endings automatically

### Mac/Linux compatibility

This command works on Mac and Linux as well. The `gh api -q` approach is universal across all platforms.

### Exit code 126: Permission denied

**Cause**: Complex multi-line commands with redirections can fail in agent/sandbox environments.

**Solution**: Use the documented Section 6 workflow (designed for these environments). Avoid creating ad-hoc command variations.

### Exit code 3: jq syntax error

**Cause**: Escaping operators that don't need escaping (e.g., `\!=` instead of `!=`).

**Fix**: In jq expressions, use `!=` not `\!=`. The documented commands use correct syntax.
