"""GoodToMerge - Deterministic PR readiness detection for AI agents.

GoodToMerge is a Python library (with thin CLI wrapper) that answers the question:
"Is this PR ready to merge?" It provides deterministic, rule-based analysis of
CI status, comments, and review threads without requiring AI inference.

Usage:
    from goodtogo import PRAnalyzer, Container, PRStatus

    container = Container.create_default(github_token="ghp_...")
    analyzer = PRAnalyzer(container)
    result = analyzer.analyze(owner="myorg", repo="myrepo", pr_number=123)

    if result.status == PRStatus.READY:
        print("PR is ready to merge!")
    else:
        for item in result.action_items:
            print(f"- {item}")

Exit Codes (CLI):
    0 - READY: All clear, PR ready to merge
    1 - ACTION_REQUIRED: Actionable comments need addressing
    2 - UNRESOLVED_THREADS: Unresolved review threads exist
    3 - CI_FAILING: CI/CD checks are failing or pending
    4 - ERROR: Error fetching data from GitHub

For more information, see: https://github.com/dsifry/goodtogo
"""

from goodtogo.container import Container
from goodtogo.core.analyzer import PRAnalyzer
from goodtogo.core.models import (
    CacheStats,
    CICheck,
    CIStatus,
    Comment,
    CommentClassification,
    PRAnalysisResult,
    Priority,
    PRStatus,
    ReviewerType,
    ThreadSummary,
)

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "PRAnalyzer",
    "Container",
    # Result models
    "PRAnalysisResult",
    "PRStatus",
    # Comment models
    "Comment",
    "CommentClassification",
    "Priority",
    "ReviewerType",
    # CI models
    "CIStatus",
    "CICheck",
    # Thread models
    "ThreadSummary",
    # Cache models
    "CacheStats",
]
