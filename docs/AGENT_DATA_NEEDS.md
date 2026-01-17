# Agent Workflow Data Needs Investigation

This document analyzes what data the agent workflows (`handle-pr-comments`, `pr-shepherd`) need from `gtg` and identifies gaps between current functionality and workflow requirements.

## Executive Summary

The current `gtg` output covers approximately **70-80%** of what agent workflows need. The primary gaps are:

1. **Reply tracking** - Workflows need to know which comments already have replies
2. **Comment-to-thread mapping** - Essential for posting replies and resolving threads
3. **Reviewer categories** - Priority-based filtering for triage
4. **Timestamp comparisons** - Detecting new comments since last action
5. **Outside-diff-range comments** - Comments in review bodies (not threads)

## 1. handle-pr-comments Workflow Analysis

### What the Workflow Does

The `handle-pr-comments` workflow systematically addresses PR review comments through:
- Discovering and filtering actionable comments
- Triaging by priority
- Making code fixes
- Posting replies to each comment thread
- Resolving threads after reviewer approval

### Data Currently Needed (from workflow documentation)

| Data Field | Purpose | Currently in gtg? | Notes |
|------------|---------|-------------------|-------|
| Comment ID | Post replies to specific comments | Yes (`Comment.id`) | Available |
| Thread ID | Resolve threads via GraphQL | Yes (`Comment.thread_id`, `UnresolvedThread.id`) | Available |
| File path | Identify location of issue | Yes (`Comment.file_path`) | Available |
| Line number | Identify location of issue | Yes (`Comment.line_number`) | Available |
| Author username | Attribution in responses | Yes (`Comment.author`) | Available |
| Comment body | Understand the feedback | Yes (`Comment.body`) | Available |
| Priority level | Triage order | Yes (`Comment.priority`) | Available |
| Classification | Actionable vs non-actionable | Yes (`Comment.classification`) | Available |
| Thread resolution status | Know if already resolved | Yes (`Comment.is_resolved`) | Available |
| Comment URL | Link for reference | Yes (`Comment.url`) | Available |
| Created timestamp | Detect new comments | Yes (`Comment.created_at`) | Available |
| **Reply count/has replies** | Know if comment addressed | **NO** | **GAP** |
| **In-reply-to ID** | Distinguish top-level vs replies | **NO** | **GAP** |
| **Review body comments** | Outside-diff-range feedback | **NO** | **GAP** |
| **Last reply timestamp** | Iteration detection | **NO** | **GAP** |

### Workflow-Specific Data Gaps

#### Gap 1: Reply Tracking

The workflow needs to verify all comments have been responded to:

```bash
# Workflow currently does this manually:
gh api "repos/$OWNER/$REPO/pulls/$PR/comments" --paginate \
  -q '.[] | select(.in_reply_to_id == null) | .id'  # Top-level comments

gh api "repos/$OWNER/$REPO/pulls/$PR/comments" --paginate \
  -q '.[] | select(.user.login == "$CURRENT_USER") | .in_reply_to_id'  # My replies
```

**What gtg should provide:**
- `has_reply: bool` - Whether a top-level comment has any replies
- `reply_count: int` - Number of replies to a comment
- `in_reply_to_id: Optional[str]` - For distinguishing top-level vs reply comments
- `replied_by_user: bool` - Whether current user has replied (requires auth context)

#### Gap 2: Comment-to-Thread Mapping Reference

While `gtg` provides `thread_id`, the workflow needs easy lookup:

```bash
# Workflow creates a mapping file:
TEMP_FILE="/tmp/pr_thread_mapping_${PR_NUMBER}_$$.txt"
# Format: CommentID:ThreadID:Resolved:FilePath
```

**What gtg could improve:**
- Output already includes thread_id per comment - this is sufficient
- Consider adding a `thread_mapping` summary object for quick lookup

#### Gap 3: Outside-Diff-Range Comments

CodeRabbit posts "Outside diff range" comments in review bodies, NOT as threads:

```bash
# Workflow must fetch separately:
gh api "repos/$OWNER/$REPO/pulls/$PR/reviews" --paginate | \
  jq -r '.[] | select(.body | test("Outside diff range"; "i"))'
```

**What gtg should provide:**
- `review_body_comments: list[ReviewBodyComment]` - Comments embedded in review bodies
- `outside_diff_range_items: list[OutsideDiffItem]` - Parsed actionable items from review bodies

#### Gap 4: New Comment Detection

Workflow needs to detect comments posted after last action:

```bash
# Get timestamp of your last reply
LAST_REPLY=$(gh api "repos/$OWNER/$REPO/pulls/$PR/comments" --paginate | \
  jq -r "[.[] | select(.user.login == \"$USER\") | select(.in_reply_to_id)] |
         sort_by(.created_at) | last | .created_at")

# Find comments newer than that
NEW_COUNT=$(gh api "repos/$OWNER/$REPO/pulls/$PR/comments" --paginate | \
  jq --arg time "$LAST_REPLY" '[.[] | select(.created_at > $time)] | length')
```

**What gtg should provide:**
- `comments_since(timestamp)` filtering parameter
- `new_comments_count: int` - If a reference timestamp is provided

---

## 2. pr-shepherd Workflow Analysis

### What the Workflow Does

The `pr-shepherd` workflow monitors PRs through to merge by:
- Polling CI status periodically
- Detecting new review comments
- Invoking `handle-pr-comments` when needed
- Auto-fixing simple issues (lint, types)
- Presenting options for complex issues
- Reporting when PR is ready

### Data Currently Needed (from workflow documentation)

| Data Field | Purpose | Currently in gtg? | Notes |
|------------|---------|-------------------|-------|
| Overall PR status | State machine decisions | Yes (`PRStatus`) | Available |
| CI check details | Identify failing checks | Yes (`CIStatus`, `CICheck`) | Available |
| CI check state | Overall pass/fail/pending | Yes (`CIStatus.state`) | Available |
| Individual check conclusions | Which specific checks failed | Yes (`CICheck.conclusion`) | Available |
| Check URLs | Link to logs | Yes (`CICheck.url`) | Available |
| Unresolved thread count | Completion check | Yes (`ThreadSummary.unresolved`) | Available |
| Actionable comment count | State transitions | Yes (`actionable_comments` list length) | Available |
| Action items list | User-friendly summary | Yes (`action_items`) | Available |
| Latest commit SHA | Reference for fixes | Yes (`latest_commit_sha`) | Available |
| Latest commit timestamp | Detect stale PR | Yes (`latest_commit_timestamp`) | Available |
| **Merge status** | Know if PR merged | **NO** | **GAP** |
| **PR title/description** | Context for decisions | **NO** | **GAP** |
| **PR labels** | Workflow routing | **NO** | **GAP** |
| **Requested reviewers** | Waiting for review | **NO** | **GAP** |
| **Review states** | Approved/changes requested | **NO** | **GAP** |

### Workflow-Specific Data Gaps

#### Gap 5: PR Merge Status

Workflow needs to detect when PR is merged:

```bash
# Workflow checks:
MERGED=$(gh pr view $PR_NUMBER --json merged -q .merged)
```

**What gtg should provide:**
- `is_merged: bool` - Whether PR has been merged
- `merged_at: Optional[str]` - Timestamp of merge (if merged)
- `merged_by: Optional[str]` - Who merged (if merged)

#### Gap 6: PR Metadata

Context useful for decision-making:

```bash
# Workflow might need:
gh pr view $PR --json title,body,labels,reviewRequests
```

**What gtg could provide (optional):**
- `pr_title: str` - PR title for logging/context
- `pr_labels: list[str]` - Labels for workflow routing
- `review_decision: str` - Overall review state (APPROVED, CHANGES_REQUESTED, etc.)
- `requested_reviewers: list[str]` - Who has been requested to review

#### Gap 7: Review State Summary

```bash
# Workflow might need to know:
# - Has anyone approved?
# - Are changes requested?
# - Is it awaiting review?
```

**What gtg should provide:**
- `has_approval: bool` - At least one APPROVED review
- `changes_requested: bool` - Any CHANGES_REQUESTED reviews pending
- `awaiting_review: bool` - No reviews yet from requested reviewers

---

## 3. Current gtg Output Structure

### PRAnalysisResult Fields

```python
class PRAnalysisResult(BaseModel):
    status: PRStatus                    # Final status
    pr_number: int                      # PR number
    repo_owner: str                     # Owner
    repo_name: str                      # Repo name
    latest_commit_sha: str              # Latest commit
    latest_commit_timestamp: str        # Commit timestamp
    ci_status: CIStatus                 # CI details
    threads: ThreadSummary              # Thread counts + unresolved list
    comments: list[Comment]             # All comments
    actionable_comments: list[Comment]  # Filtered actionable
    ambiguous_comments: list[Comment]   # Filtered ambiguous
    action_items: list[str]             # Human-readable actions
    needs_action: bool                  # Quick check
    cache_stats: Optional[CacheStats]   # Performance metrics
```

### Comment Fields

```python
class Comment(BaseModel):
    id: str                             # Comment ID
    author: str                         # Author username
    reviewer_type: ReviewerType         # Bot type or HUMAN
    body: str                           # Full text
    classification: CommentClassification  # ACTIONABLE/NON_ACTIONABLE/AMBIGUOUS
    priority: Priority                  # CRITICAL/MAJOR/MINOR/TRIVIAL/UNKNOWN
    requires_investigation: bool        # Needs agent review
    thread_id: Optional[str]            # Thread GraphQL ID
    is_resolved: bool                   # Thread resolved?
    is_outdated: bool                   # Code changed since comment?
    file_path: Optional[str]            # File reference
    line_number: Optional[int]          # Line reference
    created_at: str                     # Timestamp
    addressed_in_commit: Optional[str]  # Commit that addressed (if known)
    url: Optional[str]                  # GitHub URL
```

### What's Working Well

1. **Classification system** - ACTIONABLE/NON_ACTIONABLE/AMBIGUOUS covers workflow needs
2. **Priority levels** - Matches workflow triage requirements
3. **Thread tracking** - GraphQL IDs enable resolution via API
4. **CI check details** - Comprehensive for failure analysis
5. **Unresolved thread details** - `UnresolvedThread` model has all needed fields

---

## 4. Gap Summary and Recommendations

### High Priority Gaps (Blocking Workflows)

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| Reply tracking | Cannot verify all comments addressed | Add `in_reply_to_id`, `has_reply`, `reply_count` to Comment model |
| Outside-diff-range comments | Missing actionable feedback | Add `review_body_comments` or parse review bodies |
| New comment detection | Cannot do iteration checks | Add timestamp filtering or `comments_since` parameter |

### Medium Priority Gaps (Workflow Enhancement)

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| Merge status | Manual check required | Add `is_merged`, `merged_at` fields |
| Review state | Cannot check approval status | Add `has_approval`, `changes_requested` fields |
| PR metadata | Limited context | Consider adding `pr_title`, `pr_labels` |

### Low Priority Gaps (Nice to Have)

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| Requested reviewers | Cannot track review requests | Add `requested_reviewers` list |
| Comment mapping object | Convenience only | Current per-comment thread_id is sufficient |

---

## 5. Proposed Model Changes

### Comment Model Additions

```python
class Comment(BaseModel):
    # ... existing fields ...

    # NEW: Reply tracking
    in_reply_to_id: Optional[str] = None
    """ID of parent comment if this is a reply."""

    has_reply: bool = False
    """Whether this comment has any replies (for top-level comments)."""

    reply_count: int = 0
    """Number of replies to this comment."""
```

### New Models for Review Body Comments

```python
class ReviewBodyItem(BaseModel):
    """Actionable item extracted from a review body (e.g., 'Outside diff range')."""

    review_id: str
    """ID of the review containing this item."""

    author: str
    """Author of the review."""

    file_path: Optional[str]
    """File referenced, if parseable."""

    line_number: Optional[int]
    """Line referenced, if parseable."""

    content: str
    """The actionable content/suggestion."""

    review_submitted_at: str
    """Timestamp of the review."""
```

### PRAnalysisResult Additions

```python
class PRAnalysisResult(BaseModel):
    # ... existing fields ...

    # NEW: Merge status
    is_merged: bool = False
    """Whether the PR has been merged."""

    merged_at: Optional[str] = None
    """ISO 8601 timestamp of merge, if merged."""

    # NEW: Review state
    has_approval: bool = False
    """Whether at least one reviewer has approved."""

    changes_requested: bool = False
    """Whether any reviewer has requested changes (not dismissed)."""

    # NEW: Review body items
    review_body_items: list[ReviewBodyItem] = []
    """Actionable items from review bodies (outside diff range, etc.)."""

    # OPTIONAL: PR metadata
    pr_title: Optional[str] = None
    """PR title for context."""

    pr_labels: list[str] = []
    """PR labels for workflow routing."""
```

---

## 6. Implementation Priority

### Phase 1: Critical for Workflow Completion
1. Add `in_reply_to_id` to Comment model
2. Add `has_reply` and `reply_count` to Comment model
3. Add `is_merged` to PRAnalysisResult

### Phase 2: Iteration Detection
4. Add `review_body_items` for outside-diff-range comments
5. Add timestamp filtering option (`--since` parameter)

### Phase 3: Enhanced Context
6. Add `has_approval`, `changes_requested` fields
7. Add `pr_title`, `pr_labels` for routing/logging

---

## 7. Existing Fields That Are Underutilized

Some fields exist but workflows don't fully leverage them:

| Field | Exists In | Workflow Usage | Notes |
|-------|-----------|----------------|-------|
| `addressed_in_commit` | Comment | Not used | Could help track what's been fixed |
| `is_outdated` | Comment | Rarely checked | Useful for filtering stale comments |
| `cache_stats` | PRAnalysisResult | Not workflow-relevant | Performance metric only |
| `ambiguous_comments` | PRAnalysisResult | Used correctly | Triggers investigation |

---

## Conclusion

The `gtg` tool provides a solid foundation for agent workflows, but needs the following enhancements to fully support the `handle-pr-comments` and `pr-shepherd` workflows:

1. **Reply tracking** is the highest priority gap - workflows cannot verify completion without knowing which comments have responses
2. **Review body parsing** is needed for CodeRabbit's "Outside diff range" feedback
3. **Merge status** is needed for pr-shepherd to detect completion
4. **Review approval state** would improve workflow decision-making

The proposed changes maintain backward compatibility while adding the fields workflows need for full automation.
