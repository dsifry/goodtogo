"""Agent state persistence for tracking workflow actions across sessions.

This module provides SQLite-based persistence for agent actions on PRs.
Unlike the cache which stores API responses with TTL expiration, agent state
persists indefinitely to track what an agent has done (comments responded to,
threads resolved, feedback addressed) so sessions can resume without
duplicating work.

Security features:
- Database file created with 0600 permissions (owner read/write only)
- Parent directory created with 0700 permissions (owner only)
- All inputs validated before use
"""

from __future__ import annotations

import sqlite3
import stat
import warnings
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, Optional

if TYPE_CHECKING:
    from goodtogo.core.interfaces import TimeProvider


class ActionType(str, Enum):
    """Types of actions an agent can perform on a PR."""

    RESPONDED = "responded"
    """Agent responded to a comment."""

    RESOLVED = "resolved"
    """Agent resolved a review thread."""

    ADDRESSED = "addressed"
    """Agent addressed feedback in a commit."""

    DISMISSED = "dismissed"
    """Agent determined comment is non-actionable and dismissed it."""


class AgentAction(NamedTuple):
    """Record of an action taken by an agent.

    Attributes:
        pr_key: PR identifier in format "owner/repo:pr_number".
        action_type: Type of action taken.
        target_id: ID of the comment or thread acted upon.
        result_id: ID of the response (comment ID or commit SHA).
        created_at: Unix timestamp when the action was recorded.
    """

    pr_key: str
    action_type: ActionType
    target_id: str
    result_id: Optional[str]
    created_at: int


# SQL for schema creation
_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS agent_actions (
    id INTEGER PRIMARY KEY,
    pr_key TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    result_id TEXT,
    created_at INTEGER NOT NULL,
    UNIQUE(pr_key, action_type, target_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_actions_pr_key ON agent_actions(pr_key);
CREATE INDEX IF NOT EXISTS idx_agent_actions_type ON agent_actions(pr_key, action_type);
"""


class AgentState:
    """SQLite-based persistence for agent workflow state.

    Tracks what an agent has done on a PR across sessions, enabling
    session resume without duplicating work. Actions recorded include:
    - Comments responded to
    - Threads resolved
    - Feedback addressed in commits

    Example:
        >>> state = AgentState(".goodtogo/agent_state.db")
        >>> state.mark_comment_responded("owner/repo:123", "comment_1", "reply_99")
        >>> state.get_pending_comments("owner/repo:123", ["comment_1", "comment_2"])
        ['comment_2']

    Attributes:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str, time_provider: Optional[TimeProvider] = None) -> None:
        """Initialize the agent state store.

        Creates the database file with secure permissions if it doesn't exist.
        If the file exists with permissive permissions, they are tightened
        and a warning is issued.

        Args:
            db_path: Path to the SQLite database file. Parent directories
                    will be created if they don't exist.
            time_provider: Optional TimeProvider for time operations.
                          Defaults to SystemTimeProvider if not provided.

        Raises:
            OSError: If unable to create directory or set permissions.
        """
        from goodtogo.adapters.time_provider import SystemTimeProvider

        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._time_provider = time_provider or SystemTimeProvider()
        self._ensure_secure_path()
        self._init_database()

    def _ensure_secure_path(self) -> None:
        """Ensure database directory and file have secure permissions.

        Creates the directory with 0700 permissions and ensures the file
        (if it exists) has 0600 permissions. Issues a warning if existing
        permissions were too permissive.
        """
        path = Path(self.db_path)
        db_dir = path.parent

        # Create directory with secure permissions if needed
        # Skip permission modification for current directory (db_path has no dir component)
        if db_dir and db_dir != Path(".") and not db_dir.exists():
            db_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
        elif db_dir and db_dir != Path(".") and db_dir.exists():  # pragma: no branch
            # Ensure existing directory has correct permissions
            current_mode = stat.S_IMODE(db_dir.stat().st_mode)
            if current_mode != 0o700:
                db_dir.chmod(0o700)

        # Check existing file permissions and fix if necessary
        if path.exists():
            current_mode = stat.S_IMODE(path.stat().st_mode)
            # Check if group or others have any permissions
            if current_mode & (stat.S_IRWXG | stat.S_IRWXO):
                warnings.warn(
                    f"Agent state file {self.db_path} had permissive permissions "
                    f"({oct(current_mode)}). Fixing to 0600.",
                    UserWarning,
                    stacklevel=2,
                )
                path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def _init_database(self) -> None:
        """Initialize the database schema.

        Creates the agent_actions table if it doesn't exist.
        Sets file permissions to 0600 after creation.
        """
        conn = self._get_connection()
        conn.executescript(_CREATE_TABLES_SQL)
        conn.commit()

        # Ensure file has correct permissions after creation
        path = Path(self.db_path)
        if path.exists():  # pragma: no branch
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection.

        Returns:
            Active SQLite connection with row factory set to sqlite3.Row.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def mark_comment_responded(self, pr_key: str, comment_id: str, response_id: str) -> None:
        """Record that the agent responded to a comment.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            comment_id: ID of the comment that was responded to.
            response_id: ID of the response comment created.
        """
        self._record_action(pr_key, ActionType.RESPONDED, comment_id, response_id)

    def mark_thread_resolved(self, pr_key: str, thread_id: str) -> None:
        """Record that the agent resolved a review thread.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            thread_id: ID of the thread that was resolved.
        """
        self._record_action(pr_key, ActionType.RESOLVED, thread_id, None)

    def mark_comment_addressed(self, pr_key: str, comment_id: str, commit_sha: str) -> None:
        """Record that the agent addressed feedback in a commit.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            comment_id: ID of the comment with feedback that was addressed.
            commit_sha: SHA of the commit that addressed the feedback.
        """
        self._record_action(pr_key, ActionType.ADDRESSED, comment_id, commit_sha)

    def dismiss_comment(self, pr_key: str, comment_id: str, reason: Optional[str] = None) -> None:
        """Record that a comment was investigated and determined non-actionable.

        Use this when a comment has been evaluated and the agent determined
        no action is needed. This persists the decision so future runs skip
        re-evaluation.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            comment_id: ID of the comment being dismissed.
            reason: Optional explanation for why the comment was dismissed.
        """
        self._record_action(pr_key, ActionType.DISMISSED, comment_id, reason)

    def is_comment_dismissed(self, pr_key: str, comment_id: str) -> bool:
        """Check if a comment has been dismissed.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            comment_id: ID of the comment to check.

        Returns:
            True if the comment was previously dismissed, False otherwise.
        """
        dismissed = self._get_acted_upon_targets(pr_key, ActionType.DISMISSED)
        return comment_id in dismissed

    def get_dismissed_comments(self, pr_key: str) -> list[str]:
        """Get all comment IDs that have been dismissed.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".

        Returns:
            List of comment IDs that have been dismissed.
        """
        dismissed = self._get_acted_upon_targets(pr_key, ActionType.DISMISSED)
        return list(dismissed)

    def _record_action(
        self,
        pr_key: str,
        action_type: ActionType,
        target_id: str,
        result_id: Optional[str],
    ) -> None:
        """Record an agent action.

        Uses INSERT OR REPLACE to handle duplicate actions (e.g., if the same
        comment is responded to multiple times, the latest response is kept).

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            action_type: Type of action taken.
            target_id: ID of the comment or thread acted upon.
            result_id: ID of the response (comment ID or commit SHA).
        """
        conn = self._get_connection()
        current_time = self._time_provider.now_int()

        # Use ON CONFLICT to preserve original created_at timestamp
        # Only update result_id when re-recording the same action
        conn.execute(
            """
            INSERT INTO agent_actions
            (pr_key, action_type, target_id, result_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(pr_key, action_type, target_id) DO UPDATE SET
                result_id = excluded.result_id
            """,
            (pr_key, action_type.value, target_id, result_id, current_time),
        )
        conn.commit()

    def get_pending_comments(
        self, pr_key: str, all_comment_ids: Optional[list[str]] = None
    ) -> list[str]:
        """Get comment IDs that haven't been handled.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            all_comment_ids: List of all current comment IDs on the PR.
                If None, returns an empty list.

        Returns:
            List of comment IDs that have not been responded to, addressed,
            or dismissed.
        """
        if all_comment_ids is None:
            return []

        responded = self._get_acted_upon_targets(pr_key, ActionType.RESPONDED)
        addressed = self._get_acted_upon_targets(pr_key, ActionType.ADDRESSED)
        dismissed = self._get_acted_upon_targets(pr_key, ActionType.DISMISSED)
        handled = responded | addressed | dismissed

        return [cid for cid in all_comment_ids if cid not in handled]

    def get_pending_threads(
        self, pr_key: str, all_thread_ids: Optional[list[str]] = None
    ) -> list[str]:
        """Get thread IDs that haven't been resolved.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            all_thread_ids: List of all current thread IDs on the PR.
                If None, returns an empty list.

        Returns:
            List of thread IDs that have not been resolved.
        """
        if all_thread_ids is None:
            return []

        resolved = self._get_acted_upon_targets(pr_key, ActionType.RESOLVED)
        return [tid for tid in all_thread_ids if tid not in resolved]

    def _get_acted_upon_targets(self, pr_key: str, action_type: ActionType) -> set[str]:
        """Get all target IDs that have been acted upon.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            action_type: Type of action to query.

        Returns:
            Set of target IDs (comment or thread) that have been acted upon.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT target_id FROM agent_actions
            WHERE pr_key = ? AND action_type = ?
            """,
            (pr_key, action_type.value),
        )
        return {row["target_id"] for row in cursor.fetchall()}

    def get_responded_comments(self, pr_key: str) -> set[str]:
        """Get all comment IDs that have been responded to.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".

        Returns:
            Set of comment IDs that have been responded to.
        """
        return self._get_acted_upon_targets(pr_key, ActionType.RESPONDED)

    def get_resolved_threads(self, pr_key: str) -> set[str]:
        """Get all thread IDs that have been resolved.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".

        Returns:
            Set of thread IDs that have been resolved.
        """
        return self._get_acted_upon_targets(pr_key, ActionType.RESOLVED)

    def get_addressed_comments(self, pr_key: str) -> set[str]:
        """Get all comment IDs that have been addressed in commits.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".

        Returns:
            Set of comment IDs that have been addressed.
        """
        return self._get_acted_upon_targets(pr_key, ActionType.ADDRESSED)

    def get_actions_for_pr(self, pr_key: str) -> list[AgentAction]:
        """Get all actions recorded for a PR.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".

        Returns:
            List of AgentAction records for the PR, ordered by created_at.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT pr_key, action_type, target_id, result_id, created_at
            FROM agent_actions
            WHERE pr_key = ?
            ORDER BY created_at
            """,
            (pr_key,),
        )
        return [
            AgentAction(
                pr_key=row["pr_key"],
                action_type=ActionType(row["action_type"]),
                target_id=row["target_id"],
                result_id=row["result_id"],
                created_at=row["created_at"],
            )
            for row in cursor.fetchall()
        ]

    def get_progress_summary(
        self,
        pr_key: str,
        total_comments: int,
        total_threads: int,
    ) -> dict[str, int]:
        """Get a progress summary for a PR.

        Useful for reporting "X of Y comments addressed" style progress.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".
            total_comments: Total number of comments on the PR.
            total_threads: Total number of threads on the PR.

        Returns:
            Dictionary with progress counts:
            - comments_responded: Number of comments responded to
            - comments_addressed: Number of comments addressed in commits
            - comments_total: Total comments (echoed back)
            - threads_resolved: Number of threads resolved
            - threads_total: Total threads (echoed back)
        """
        conn = self._get_connection()

        # Count distinct targets for each action type
        cursor = conn.execute(
            """
            SELECT action_type, COUNT(DISTINCT target_id) as count
            FROM agent_actions
            WHERE pr_key = ?
            GROUP BY action_type
            """,
            (pr_key,),
        )
        counts = {row["action_type"]: row["count"] for row in cursor.fetchall()}

        return {
            "comments_responded": counts.get(ActionType.RESPONDED.value, 0),
            "comments_addressed": counts.get(ActionType.ADDRESSED.value, 0),
            "comments_total": total_comments,
            "threads_resolved": counts.get(ActionType.RESOLVED.value, 0),
            "threads_total": total_threads,
        }

    def clear_pr_actions(self, pr_key: str) -> int:
        """Clear all recorded actions for a PR.

        Useful when starting fresh on a PR or when the PR is closed/merged.

        Args:
            pr_key: PR identifier in format "owner/repo:pr_number".

        Returns:
            Number of actions deleted.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM agent_actions WHERE pr_key = ?",
            (pr_key,),
        )
        conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        """Close the database connection.

        Should be called when the state store is no longer needed to release
        database resources.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __del__(self) -> None:
        """Ensure connection is closed on garbage collection."""
        self.close()

    def __repr__(self) -> str:
        """Return string representation of the state store."""
        return f"AgentState(db_path={self.db_path!r})"
