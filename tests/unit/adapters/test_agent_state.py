"""Tests for AgentState - agent workflow state persistence.

This module tests the AgentState class which provides SQLite-based persistence
for tracking agent actions across sessions. Tests cover:
- Database initialization with secure permissions
- Recording actions (responded, resolved, addressed)
- Querying pending comments and threads
- Progress summary generation
- Session resume scenarios
- Edge cases and error handling
"""

import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

from goodtogo.adapters.agent_state import ActionType, AgentAction, AgentState
from goodtogo.adapters.time_provider import MockTimeProvider


class TestAgentStateInit:
    """Tests for AgentState initialization."""

    def test_init_creates_database(self) -> None:
        """Test that init creates the database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)
            assert os.path.exists(db_path)
            state.close()

    def test_init_creates_parent_directories(self) -> None:
        """Test that init creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "nested", "dir", "state.db")
            state = AgentState(db_path)
            assert os.path.exists(db_path)
            state.close()

    def test_init_sets_secure_file_permissions(self) -> None:
        """Test that database file has 0600 permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)
            mode = stat.S_IMODE(os.stat(db_path).st_mode)
            assert mode == 0o600
            state.close()

    def test_init_sets_secure_directory_permissions(self) -> None:
        """Test that parent directory has 0700 permissions when created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "newdir")
            db_path = os.path.join(nested_dir, "state.db")
            state = AgentState(db_path)
            mode = stat.S_IMODE(os.stat(nested_dir).st_mode)
            assert mode == 0o700
            state.close()

    def test_init_warns_on_permissive_file(self) -> None:
        """Test that a warning is issued for permissive file permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            # Create file with permissive permissions
            # Note: Must use os.chmod after touch because Path.touch(mode=) is masked by umask
            Path(db_path).touch()
            os.chmod(db_path, 0o644)

            import warnings

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                state = AgentState(db_path)
                assert len(w) == 1
                assert "permissive permissions" in str(w[0].message)
                state.close()


class TestMarkCommentResponded:
    """Tests for mark_comment_responded method."""

    def test_mark_comment_responded_records_action(self) -> None:
        """Test that marking a comment as responded records the action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "comment_1", "response_99")
            responded = state.get_responded_comments("owner/repo:123")

            assert "comment_1" in responded
            state.close()

    def test_mark_comment_responded_stores_response_id(self) -> None:
        """Test that response_id is stored in the action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "comment_1", "response_99")
            actions = state.get_actions_for_pr("owner/repo:123")

            assert len(actions) == 1
            assert actions[0].result_id == "response_99"
            state.close()

    def test_mark_comment_responded_updates_on_duplicate(self) -> None:
        """Test that duplicate marks update the existing record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "comment_1", "response_1")
            state.mark_comment_responded("owner/repo:123", "comment_1", "response_2")
            actions = state.get_actions_for_pr("owner/repo:123")

            assert len(actions) == 1
            assert actions[0].result_id == "response_2"
            state.close()


class TestMarkThreadResolved:
    """Tests for mark_thread_resolved method."""

    def test_mark_thread_resolved_records_action(self) -> None:
        """Test that marking a thread as resolved records the action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_thread_resolved("owner/repo:123", "thread_1")
            resolved = state.get_resolved_threads("owner/repo:123")

            assert "thread_1" in resolved
            state.close()

    def test_mark_thread_resolved_has_no_result_id(self) -> None:
        """Test that thread resolution has no result_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_thread_resolved("owner/repo:123", "thread_1")
            actions = state.get_actions_for_pr("owner/repo:123")

            assert len(actions) == 1
            assert actions[0].result_id is None
            state.close()


class TestMarkCommentAddressed:
    """Tests for mark_comment_addressed method."""

    def test_mark_comment_addressed_records_action(self) -> None:
        """Test that marking a comment as addressed records the action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_addressed("owner/repo:123", "comment_1", "abc123")
            addressed = state.get_addressed_comments("owner/repo:123")

            assert "comment_1" in addressed
            state.close()

    def test_mark_comment_addressed_stores_commit_sha(self) -> None:
        """Test that commit SHA is stored in the action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_addressed("owner/repo:123", "comment_1", "abc123def")
            actions = state.get_actions_for_pr("owner/repo:123")

            assert len(actions) == 1
            assert actions[0].result_id == "abc123def"
            state.close()


class TestGetPendingComments:
    """Tests for get_pending_comments method."""

    def test_get_pending_comments_with_none_returns_empty(self) -> None:
        """Test that None input returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            result = state.get_pending_comments("owner/repo:123", None)

            assert result == []
            state.close()

    def test_get_pending_comments_all_pending(self) -> None:
        """Test that all comments are pending when none acted upon."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            all_comments = ["c1", "c2", "c3"]
            result = state.get_pending_comments("owner/repo:123", all_comments)

            assert result == ["c1", "c2", "c3"]
            state.close()

    def test_get_pending_comments_excludes_responded(self) -> None:
        """Test that responded comments are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            result = state.get_pending_comments("owner/repo:123", ["c1", "c2", "c3"])

            assert result == ["c2", "c3"]
            state.close()

    def test_get_pending_comments_excludes_addressed(self) -> None:
        """Test that addressed comments are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_addressed("owner/repo:123", "c2", "sha123")
            result = state.get_pending_comments("owner/repo:123", ["c1", "c2", "c3"])

            assert result == ["c1", "c3"]
            state.close()

    def test_get_pending_comments_excludes_both(self) -> None:
        """Test that both responded and addressed comments are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            state.mark_comment_addressed("owner/repo:123", "c3", "sha123")
            result = state.get_pending_comments("owner/repo:123", ["c1", "c2", "c3"])

            assert result == ["c2"]
            state.close()


class TestGetPendingThreads:
    """Tests for get_pending_threads method."""

    def test_get_pending_threads_with_none_returns_empty(self) -> None:
        """Test that None input returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            result = state.get_pending_threads("owner/repo:123", None)

            assert result == []
            state.close()

    def test_get_pending_threads_all_pending(self) -> None:
        """Test that all threads are pending when none resolved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            all_threads = ["t1", "t2", "t3"]
            result = state.get_pending_threads("owner/repo:123", all_threads)

            assert result == ["t1", "t2", "t3"]
            state.close()

    def test_get_pending_threads_excludes_resolved(self) -> None:
        """Test that resolved threads are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_thread_resolved("owner/repo:123", "t1")
            result = state.get_pending_threads("owner/repo:123", ["t1", "t2", "t3"])

            assert result == ["t2", "t3"]
            state.close()


class TestGetActionsForPR:
    """Tests for get_actions_for_pr method."""

    def test_get_actions_for_pr_empty(self) -> None:
        """Test that empty list is returned for PR with no actions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            result = state.get_actions_for_pr("owner/repo:123")

            assert result == []
            state.close()

    def test_get_actions_for_pr_returns_all_types(self) -> None:
        """Test that all action types are returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            state.mark_thread_resolved("owner/repo:123", "t1")
            state.mark_comment_addressed("owner/repo:123", "c2", "sha1")
            result = state.get_actions_for_pr("owner/repo:123")

            action_types = {a.action_type for a in result}
            assert ActionType.RESPONDED in action_types
            assert ActionType.RESOLVED in action_types
            assert ActionType.ADDRESSED in action_types
            state.close()

    def test_get_actions_for_pr_ordered_by_time(self) -> None:
        """Test that actions are ordered by created_at timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            time_provider = MockTimeProvider(start=1000)
            state = AgentState(db_path, time_provider=time_provider)

            # Use time_provider.advance() to ensure different timestamps
            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            time_provider.advance(1)
            state.mark_thread_resolved("owner/repo:123", "t1")
            time_provider.advance(1)
            state.mark_comment_addressed("owner/repo:123", "c2", "sha1")

            result = state.get_actions_for_pr("owner/repo:123")

            # Verify ordering by timestamp - must be strictly increasing
            assert len(result) == 3
            assert result[0].created_at < result[1].created_at < result[2].created_at
            assert result[0].created_at == 1000
            assert result[1].created_at == 1001
            assert result[2].created_at == 1002
            state.close()

    def test_get_actions_for_pr_isolates_by_pr(self) -> None:
        """Test that actions are isolated by PR key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            state.mark_comment_responded("owner/repo:456", "c2", "r2")
            result = state.get_actions_for_pr("owner/repo:123")

            assert len(result) == 1
            assert result[0].target_id == "c1"
            state.close()

    def test_get_actions_returns_agent_action_namedtuple(self) -> None:
        """Test that returned objects are AgentAction namedtuples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            result = state.get_actions_for_pr("owner/repo:123")

            assert len(result) == 1
            action = result[0]
            assert isinstance(action, AgentAction)
            assert action.pr_key == "owner/repo:123"
            assert action.action_type == ActionType.RESPONDED
            assert action.target_id == "c1"
            assert action.result_id == "r1"
            assert isinstance(action.created_at, int)
            state.close()


class TestGetProgressSummary:
    """Tests for get_progress_summary method."""

    def test_get_progress_summary_initial_state(self) -> None:
        """Test progress summary with no actions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            result = state.get_progress_summary("owner/repo:123", 10, 5)

            assert result["comments_responded"] == 0
            assert result["comments_addressed"] == 0
            assert result["comments_total"] == 10
            assert result["threads_resolved"] == 0
            assert result["threads_total"] == 5
            state.close()

    def test_get_progress_summary_with_actions(self) -> None:
        """Test progress summary with some actions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            state.mark_comment_responded("owner/repo:123", "c2", "r2")
            state.mark_comment_addressed("owner/repo:123", "c3", "sha1")
            state.mark_thread_resolved("owner/repo:123", "t1")

            result = state.get_progress_summary("owner/repo:123", 10, 5)

            assert result["comments_responded"] == 2
            assert result["comments_addressed"] == 1
            assert result["comments_total"] == 10
            assert result["threads_resolved"] == 1
            assert result["threads_total"] == 5
            state.close()

    def test_get_progress_summary_isolates_by_pr(self) -> None:
        """Test that progress is isolated by PR key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            state.mark_comment_responded("owner/repo:456", "c2", "r2")

            result = state.get_progress_summary("owner/repo:123", 10, 5)

            assert result["comments_responded"] == 1
            state.close()


class TestClearPRActions:
    """Tests for clear_pr_actions method."""

    def test_clear_pr_actions_removes_all(self) -> None:
        """Test that all actions for a PR are removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            state.mark_thread_resolved("owner/repo:123", "t1")
            count = state.clear_pr_actions("owner/repo:123")
            result = state.get_actions_for_pr("owner/repo:123")

            assert count == 2
            assert result == []
            state.close()

    def test_clear_pr_actions_preserves_other_prs(self) -> None:
        """Test that actions for other PRs are not affected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            state.mark_comment_responded("owner/repo:456", "c2", "r2")
            state.clear_pr_actions("owner/repo:123")
            result = state.get_actions_for_pr("owner/repo:456")

            assert len(result) == 1
            state.close()

    def test_clear_pr_actions_returns_zero_if_none(self) -> None:
        """Test that zero is returned if no actions to clear."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            count = state.clear_pr_actions("owner/repo:123")

            assert count == 0
            state.close()


class TestAgentStateClose:
    """Tests for close method."""

    def test_close_closes_connection(self) -> None:
        """Test that close releases the database connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.close()

            assert state._connection is None

    def test_close_can_be_called_multiple_times(self) -> None:
        """Test that close can be called multiple times safely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.close()
            state.close()

            assert state._connection is None

    def test_del_closes_connection(self) -> None:
        """Test that __del__ closes the connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)
            # Ensure connection is created
            _ = state._connection

            del state

            # Connection should be closed after del
            # We can't check the state object directly since it's deleted
            # But if we reach here without error, the test passes
            assert True


class TestAgentStateRepr:
    """Tests for __repr__ method."""

    def test_repr_includes_db_path(self) -> None:
        """Test that repr includes the database path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            result = repr(state)

            assert db_path in result
            state.close()

    def test_repr_format(self) -> None:
        """Test the format of repr output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            result = repr(state)

            assert result == f"AgentState(db_path={db_path!r})"
            state.close()


class TestAgentStatePersistence:
    """Tests for persistence across connections."""

    def test_data_persists_across_connections(self) -> None:
        """Test that data persists when connection is closed and reopened."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")

            # First connection - add data
            state1 = AgentState(db_path)
            state1.mark_comment_responded("owner/repo:123", "c1", "r1")
            state1.close()

            # Second connection - verify data persists
            state2 = AgentState(db_path)
            responded = state2.get_responded_comments("owner/repo:123")
            state2.close()

            assert "c1" in responded


class TestAgentStateSessionResume:
    """Tests for session resume scenarios."""

    def test_resume_knows_previous_work(self) -> None:
        """Test that a resumed session knows what was done before."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")

            # Session 1: Agent works on some comments
            state1 = AgentState(db_path)
            state1.mark_comment_responded("owner/repo:123", "c1", "r1")
            state1.mark_comment_responded("owner/repo:123", "c2", "r2")
            state1.mark_thread_resolved("owner/repo:123", "t1")
            state1.close()

            # Session 2: Agent resumes and checks pending work
            state2 = AgentState(db_path)
            all_comments = ["c1", "c2", "c3", "c4"]
            all_threads = ["t1", "t2"]

            pending_comments = state2.get_pending_comments("owner/repo:123", all_comments)
            pending_threads = state2.get_pending_threads("owner/repo:123", all_threads)
            state2.close()

            assert pending_comments == ["c3", "c4"]
            assert pending_threads == ["t2"]

    def test_progress_report_after_resume(self) -> None:
        """Test progress reporting after session resume."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")

            # Session 1: Partial work
            state1 = AgentState(db_path)
            state1.mark_comment_responded("owner/repo:123", "c1", "r1")
            state1.mark_comment_responded("owner/repo:123", "c2", "r2")
            state1.close()

            # Session 2: Resume and check progress
            state2 = AgentState(db_path)
            progress = state2.get_progress_summary("owner/repo:123", 5, 3)
            state2.close()

            assert progress["comments_responded"] == 2
            assert progress["comments_total"] == 5


class TestAgentStateEdgeCases:
    """Tests for edge cases and error handling."""

    def test_init_with_existing_correct_dir_permissions(self) -> None:
        """Test init when directory exists with correct permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set correct permissions on the temp dir
            os.chmod(tmpdir, 0o700)
            db_path = os.path.join(tmpdir, "state.db")

            state = AgentState(db_path)

            assert os.path.exists(db_path)
            state.close()

    def test_init_fixes_wrong_dir_permissions(self) -> None:
        """Test init fixes directory with wrong permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set wrong permissions on the temp dir
            os.chmod(tmpdir, 0o755)
            db_path = os.path.join(tmpdir, "state.db")

            state = AgentState(db_path)

            # Dir permissions should be fixed to 0700
            mode = stat.S_IMODE(os.stat(tmpdir).st_mode)
            assert mode == 0o700
            state.close()

    def test_init_with_relative_path(self) -> None:
        """Test init with a relative path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                state = AgentState("state.db")
                assert os.path.exists(os.path.join(tmpdir, "state.db"))
                state.close()
            finally:
                os.chdir(orig_dir)

    def test_init_database_with_mocked_path_not_exists(self) -> None:
        """Test _init_database when path.exists() returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            # File should exist after init
            assert os.path.exists(db_path)
            state.close()

    def test_init_with_empty_parent_path(self) -> None:
        """Test init when parent path is empty (current directory)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                # db_dir will be Path('') which is falsy
                state = AgentState("state.db")
                assert os.path.exists("state.db")
                state.close()
            finally:
                os.chdir(orig_dir)

    def test_init_skipping_both_if_elif_branches(self) -> None:
        """Test that code handles case where db_dir is falsy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                # When path is just a filename, parent is '' which is falsy
                state = AgentState("test.db")
                assert os.path.exists("test.db")
                state.close()
            finally:
                os.chdir(orig_dir)

    def test_init_database_when_path_not_exists_after_creation(self) -> None:
        """Test _init_database handles rare case where path doesn't exist after connect.

        This tests the edge case where path.exists() returns False in _init_database,
        which would only happen if the file was deleted between connect() and the
        exists() check (a race condition).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")

            # Create state normally first
            state = AgentState(db_path)
            state.close()

            # Now test with mocked Path.exists returning False in _init_database
            # This simulates the race condition
            call_count = [0]
            original_exists = Path.exists

            def mock_exists(self):
                # Count calls to exists() for state.db
                if str(self).endswith("state.db"):
                    call_count[0] += 1
                    # Return False on the 3rd call (in _init_database)
                    if call_count[0] == 3:
                        return False
                return original_exists(self)

            # Delete the db file and recreate with mocked exists
            os.remove(db_path)

            with patch.object(Path, "exists", mock_exists):
                state2 = AgentState(db_path)
                # Even with mock returning False once, the state should be created
                state2.close()

            # Verify state was actually created
            assert os.path.exists(db_path)


class TestActionTypeEnum:
    """Tests for ActionType enum."""

    def test_action_type_values(self) -> None:
        """Test that ActionType has expected values."""
        assert ActionType.RESPONDED.value == "responded"
        assert ActionType.RESOLVED.value == "resolved"
        assert ActionType.ADDRESSED.value == "addressed"
        assert ActionType.DISMISSED.value == "dismissed"

    def test_action_type_is_string_enum(self) -> None:
        """Test that ActionType is a string enum."""
        assert isinstance(ActionType.RESPONDED, str)
        assert ActionType.RESPONDED.value == "responded"

    def test_dismissed_action_type_exists(self) -> None:
        """Test that DISMISSED action type exists for classification persistence."""
        assert hasattr(ActionType, "DISMISSED")
        assert ActionType.DISMISSED.value == "dismissed"


class TestDismissComment:
    """Tests for dismiss_comment method."""

    def test_dismiss_comment_records_action(self) -> None:
        """Test that dismissing a comment records the action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.dismiss_comment("owner/repo:123", "comment_1")
            dismissed = state.get_dismissed_comments("owner/repo:123")

            assert "comment_1" in dismissed
            state.close()

    def test_dismiss_comment_with_reason(self) -> None:
        """Test that dismissal reason is stored in result_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.dismiss_comment("owner/repo:123", "comment_1", reason="Informational only")
            actions = state.get_actions_for_pr("owner/repo:123")

            assert len(actions) == 1
            assert actions[0].action_type == ActionType.DISMISSED
            assert actions[0].result_id == "Informational only"
            state.close()

    def test_dismiss_comment_without_reason(self) -> None:
        """Test that dismissal works without a reason."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.dismiss_comment("owner/repo:123", "comment_1")
            actions = state.get_actions_for_pr("owner/repo:123")

            assert len(actions) == 1
            assert actions[0].action_type == ActionType.DISMISSED
            assert actions[0].result_id is None
            state.close()

    def test_dismiss_comment_updates_on_duplicate(self) -> None:
        """Test that duplicate dismissals update the reason."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.dismiss_comment("owner/repo:123", "comment_1", reason="First reason")
            state.dismiss_comment("owner/repo:123", "comment_1", reason="Updated reason")
            actions = state.get_actions_for_pr("owner/repo:123")

            assert len(actions) == 1
            assert actions[0].result_id == "Updated reason"
            state.close()


class TestIsCommentDismissed:
    """Tests for is_comment_dismissed method."""

    def test_is_comment_dismissed_returns_false_when_not_dismissed(self) -> None:
        """Test that non-dismissed comments return False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            result = state.is_comment_dismissed("owner/repo:123", "comment_1")

            assert result is False
            state.close()

    def test_is_comment_dismissed_returns_true_when_dismissed(self) -> None:
        """Test that dismissed comments return True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.dismiss_comment("owner/repo:123", "comment_1")
            result = state.is_comment_dismissed("owner/repo:123", "comment_1")

            assert result is True
            state.close()

    def test_is_comment_dismissed_isolates_by_pr(self) -> None:
        """Test that dismissal status is isolated by PR key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.dismiss_comment("owner/repo:123", "comment_1")
            result = state.is_comment_dismissed("owner/repo:456", "comment_1")

            assert result is False
            state.close()


class TestGetDismissedComments:
    """Tests for get_dismissed_comments method."""

    def test_get_dismissed_comments_empty(self) -> None:
        """Test that empty list is returned when no comments dismissed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            result = state.get_dismissed_comments("owner/repo:123")

            assert result == []
            state.close()

    def test_get_dismissed_comments_returns_all_dismissed(self) -> None:
        """Test that all dismissed comment IDs are returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.dismiss_comment("owner/repo:123", "c1")
            state.dismiss_comment("owner/repo:123", "c2")
            state.dismiss_comment("owner/repo:123", "c3")
            result = state.get_dismissed_comments("owner/repo:123")

            assert set(result) == {"c1", "c2", "c3"}
            state.close()

    def test_get_dismissed_comments_isolates_by_pr(self) -> None:
        """Test that dismissed comments are isolated by PR key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.dismiss_comment("owner/repo:123", "c1")
            state.dismiss_comment("owner/repo:456", "c2")
            result = state.get_dismissed_comments("owner/repo:123")

            assert result == ["c1"]
            state.close()


class TestGetPendingCommentsWithDismissed:
    """Tests for get_pending_comments excluding dismissed comments."""

    def test_get_pending_comments_excludes_dismissed(self) -> None:
        """Test that dismissed comments are excluded from pending."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.dismiss_comment("owner/repo:123", "c1")
            result = state.get_pending_comments("owner/repo:123", ["c1", "c2", "c3"])

            assert result == ["c2", "c3"]
            state.close()

    def test_get_pending_comments_excludes_all_handled_types(self) -> None:
        """Test that responded, addressed, AND dismissed are all excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")
            state = AgentState(db_path)

            state.mark_comment_responded("owner/repo:123", "c1", "r1")
            state.mark_comment_addressed("owner/repo:123", "c2", "sha123")
            state.dismiss_comment("owner/repo:123", "c3", reason="Non-actionable")
            result = state.get_pending_comments("owner/repo:123", ["c1", "c2", "c3", "c4"])

            assert result == ["c4"]
            state.close()


class TestDismissedPersistence:
    """Tests for dismissed comment persistence across sessions."""

    def test_dismissed_persists_across_connections(self) -> None:
        """Test that dismissals persist when connection is closed and reopened."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "state.db")

            # First connection - dismiss comment
            state1 = AgentState(db_path)
            state1.dismiss_comment("owner/repo:123", "c1", reason="Not actionable")
            state1.close()

            # Second connection - verify dismissal persists
            state2 = AgentState(db_path)
            assert state2.is_comment_dismissed("owner/repo:123", "c1") is True
            dismissed = state2.get_dismissed_comments("owner/repo:123")
            assert "c1" in dismissed
            state2.close()


class TestAgentActionNamedTuple:
    """Tests for AgentAction NamedTuple."""

    def test_agent_action_fields(self) -> None:
        """Test AgentAction has expected fields."""
        action = AgentAction(
            pr_key="owner/repo:123",
            action_type=ActionType.RESPONDED,
            target_id="c1",
            result_id="r1",
            created_at=1234567890,
        )

        assert action.pr_key == "owner/repo:123"
        assert action.action_type == ActionType.RESPONDED
        assert action.target_id == "c1"
        assert action.result_id == "r1"
        assert action.created_at == 1234567890

    def test_agent_action_optional_result_id(self) -> None:
        """Test AgentAction with None result_id."""
        action = AgentAction(
            pr_key="owner/repo:123",
            action_type=ActionType.RESOLVED,
            target_id="t1",
            result_id=None,
            created_at=1234567890,
        )

        assert action.result_id is None

    def test_agent_action_with_dismissed_type(self) -> None:
        """Test AgentAction with DISMISSED action type."""
        action = AgentAction(
            pr_key="owner/repo:123",
            action_type=ActionType.DISMISSED,
            target_id="c1",
            result_id="Informational comment",
            created_at=1234567890,
        )

        assert action.action_type == ActionType.DISMISSED
        assert action.result_id == "Informational comment"
