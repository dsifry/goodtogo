"""Thin CLI wrapper around PRAnalyzer.

This module provides a command-line interface for the GoodToMerge library,
enabling AI agents and humans to check PR readiness from the terminal or
CI/CD pipelines.

Exit codes (default - AI-friendly mode):
    0 - Any analyzable state (READY, ACTION_REQUIRED, UNRESOLVED_THREADS, CI_FAILING)
    4 - Error fetching data (PRStatus.ERROR)

Exit codes (with -q or --semantic-codes):
    0 - Ready to merge (PRStatus.READY)
    1 - Actionable comments need addressing (PRStatus.ACTION_REQUIRED)
    2 - Unresolved threads exist (PRStatus.UNRESOLVED_THREADS)
    3 - CI/CD checks failing (PRStatus.CI_FAILING)
    4 - Error fetching data (PRStatus.ERROR)

Example:
    $ gtg 123                          # auto-detect repo from git origin
    $ gtg 123 --repo myorg/myrepo      # explicit repo
    $ gtg 123 --format text --verbose  # human-readable output
    $ gtg 123 -q                       # quiet mode with semantic exit codes
    $ gtg 123 --semantic-codes         # semantic exit codes with output
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Optional

import click

from goodtogo import __version__
from goodtogo.container import Container
from goodtogo.core.analyzer import PRAnalyzer
from goodtogo.core.errors import redact_error
from goodtogo.core.models import PRAnalysisResult, PRStatus


def parse_github_remote_url(url: str) -> Optional[tuple[str, str]]:
    """Parse a GitHub remote URL to extract owner and repo.

    Supports both HTTPS and SSH formats:
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo
    - git@github.com:owner/repo.git
    - git@github.com:owner/repo

    Args:
        url: The git remote URL to parse.

    Returns:
        Tuple of (owner, repo) if the URL is a valid GitHub URL,
        None otherwise.
    """
    if not url:
        return None

    # HTTPS format: https://github.com/owner/repo.git or https://github.com/owner/repo
    https_pattern = r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
    match = re.match(https_pattern, url)
    if match:
        return (match.group(1), match.group(2))

    # SSH format: git@github.com:owner/repo.git or git@github.com:owner/repo
    ssh_pattern = r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?/?$"
    match = re.match(ssh_pattern, url)
    if match:
        return (match.group(1), match.group(2))

    return None


def get_repo_from_git_origin() -> Optional[tuple[str, str]]:
    """Get repository owner and name from git remote origin.

    Runs `git remote get-url origin` to get the origin URL,
    then parses it to extract owner and repo name.

    Returns:
        Tuple of (owner, repo) if origin is a valid GitHub URL,
        None if not in a git repo, no origin remote, origin isn't GitHub,
        git is not installed, or the command times out.
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        origin_url = result.stdout.strip()
        return parse_github_remote_url(origin_url)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # No origin remote, not a git repo, git not installed, or timeout
        return None


# Semantic exit codes for shell scripting (-q or --semantic-codes)
SEMANTIC_EXIT_CODES: dict[PRStatus, int] = {
    PRStatus.READY: 0,
    PRStatus.ACTION_REQUIRED: 1,
    PRStatus.UNRESOLVED_THREADS: 2,
    PRStatus.CI_FAILING: 3,
    PRStatus.ERROR: 4,
}

# AI-friendly exit codes (default) - only ERROR is non-zero
AI_FRIENDLY_EXIT_CODES: dict[PRStatus, int] = {
    PRStatus.READY: 0,
    PRStatus.ACTION_REQUIRED: 0,
    PRStatus.UNRESOLVED_THREADS: 0,
    PRStatus.CI_FAILING: 0,
    PRStatus.ERROR: 4,
}


@click.command()
@click.argument("pr_number", type=int)
@click.option(
    "--repo",
    "-r",
    required=False,
    default=None,
    help="Repository in owner/repo format (auto-detected from git origin if not provided)",
)
@click.option(
    "--cache",
    type=click.Choice(["sqlite", "redis", "none"]),
    default="sqlite",
    help="Cache backend (default: sqlite)",
)
@click.option(
    "--cache-path",
    default=".goodtogo/cache.db",
    help="SQLite cache path",
)
@click.option(
    "--redis-url",
    envvar="REDIS_URL",
    help="Redis URL (required if --cache=redis)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "text"]),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
@click.option(
    "--exclude-checks",
    "-x",
    multiple=True,
    help="CI check names to exclude (can be repeated)",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Quiet mode: no output, use semantic exit codes (like grep -q)",
)
@click.option(
    "--semantic-codes",
    is_flag=True,
    help="Use semantic exit codes (0=ready, 1=action, 2=threads, 3=ci, 4=error)",
)
@click.version_option(version=__version__)
def main(
    pr_number: int,
    repo: Optional[str],
    cache: str,
    cache_path: str,
    redis_url: Optional[str],
    output_format: str,
    verbose: bool,
    exclude_checks: tuple[str, ...],
    quiet: bool,
    semantic_codes: bool,
) -> None:
    """Check if a PR is ready to merge.

    PR_NUMBER is the pull request number to check.

    Exit codes (default - AI-friendly):
      0 - Any analyzable state (ready, action required, threads, CI)
      4 - Error fetching data

    Exit codes (with -q or --semantic-codes):
      0 - Ready to merge
      1 - Actionable comments need addressing
      2 - Unresolved threads exist
      3 - CI/CD checks failing
      4 - Error fetching data
    """
    # Get GitHub token from environment
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        click.echo("Error: GITHUB_TOKEN environment variable required", err=True)
        sys.exit(4)

    # Determine owner/repo - either from --repo option or auto-detect from git origin
    if repo is not None:
        # Parse owner/repo from --repo option
        try:
            owner, repo_name = repo.strip().split("/")
            if not owner or not repo_name:
                raise ValueError("Empty owner or repo name")
        except ValueError:
            click.echo("Error: --repo must be in owner/repo format", err=True)
            sys.exit(4)
    else:
        # Auto-detect from git origin
        detected = get_repo_from_git_origin()
        if detected is None:
            click.echo(
                "Error: Could not detect repository from git origin. "
                "Use --repo owner/repo or run from a GitHub repository.",
                err=True,
            )
            sys.exit(4)
        owner, repo_name = detected

    # Create container and analyzer, then analyze PR
    try:
        container = Container.create_default(
            github_token=github_token,
            cache_type=cache,
            cache_path=cache_path,
            redis_url=redis_url,
        )
        analyzer = PRAnalyzer(container)
        result = analyzer.analyze(owner, repo_name, pr_number, exclude_checks=set(exclude_checks))
    except Exception as e:
        # Redact sensitive data from error messages
        redacted = redact_error(e)
        if verbose:
            click.echo(f"Error: {redacted}", err=True)
        else:
            click.echo(
                "Error: Failed to analyze PR. Use --verbose for details.",
                err=True,
            )
        sys.exit(4)

    # Determine which exit code mapping to use
    use_semantic = quiet or semantic_codes
    exit_codes = SEMANTIC_EXIT_CODES if use_semantic else AI_FRIENDLY_EXIT_CODES

    # Output result in requested format (skip if quiet mode)
    if not quiet:
        if output_format == "json":
            click.echo(result.model_dump_json(indent=2))
        else:
            _print_text_output(result, verbose)

    sys.exit(exit_codes[result.status])


def _print_text_output(result: PRAnalysisResult, verbose: bool) -> None:
    """Print human-readable output.

    Displays a formatted summary of the PR analysis result suitable
    for human consumption in the terminal.

    Args:
        result: The PR analysis result to display.
        verbose: If True, show additional details like ambiguous comments.
    """
    status_icons = {
        PRStatus.READY: "OK",
        PRStatus.ACTION_REQUIRED: "!!",
        PRStatus.UNRESOLVED_THREADS: "??",
        PRStatus.CI_FAILING: "XX",
        PRStatus.ERROR: "##",
    }

    icon = status_icons.get(result.status, "??")
    click.echo(f"{icon} PR #{result.pr_number}: {result.status.value}")
    click.echo(
        f"   CI: {result.ci_status.state} "
        f"({result.ci_status.passed}/{result.ci_status.total_checks} passed)"
    )
    click.echo(f"   Threads: {result.threads.resolved}/{result.threads.total} resolved")

    if result.action_items:
        click.echo("\nAction required:")
        for item in result.action_items:
            click.echo(f"   - {item}")

    if verbose and result.ambiguous_comments:
        click.echo("\nAmbiguous (needs investigation):")
        for comment in result.ambiguous_comments:
            # Truncate body to 80 chars for readability
            body_preview = comment.body[:80]
            if len(comment.body) > 80:
                body_preview += "..."
            click.echo(f"   - [{comment.author}] {body_preview}")


if __name__ == "__main__":  # pragma: no cover
    main()
