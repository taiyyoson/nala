"""
E2E Test Suite - Full User Flow

Tests the complete Nala Health Coach lifecycle at the API level:
  sign-up -> onboarding -> session 1 -> session 2 -> session 3 -> session 4

Uses StatefulMockAIService to simulate session state progression
without real LLM calls. Each session completes after 3 messages.

Tests are ordered sequentially within the class (session 2 depends on
session 1 completing, etc.). The final test_full_program_sequential
runs the entire flow independently in a single test.
"""

import uuid
from unittest.mock import patch

import pytest
from app import app
from fastapi.testclient import TestClient

from tests.mock_ai_service import StatefulMockFactory

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MESSAGES_PER_SESSION = 3
E2E_USER_ID = f"e2e_user_{uuid.uuid4().hex[:8]}"

# API base paths
CHAT_URL = "/api/v1/chat/message"
ONBOARDING_URL = "/api/v1/user/onboarding"
USER_STATUS_URL = "/api/v1/user/status"
SESSION_PROGRESS_URL = "/api/v1/session/progress"


# ---------------------------------------------------------------------------
# Fixtures — override the conftest autouse mock_ai_service
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_ai_service():
    """
    Override the conftest autouse mock.
    E2E tests use their own stateful mock via e2e_mock_factory.
    This fixture keeps the patch active but delegates to the factory.
    """
    # Intentionally empty — e2e_mock_factory handles patching
    yield


@pytest.fixture(scope="module")
def e2e_mock_factory():
    """Module-scoped factory so state persists across ordered tests."""
    return StatefulMockFactory(messages_per_session=MESSAGES_PER_SESSION)


@pytest.fixture(scope="module")
def e2e_client(e2e_mock_factory):
    """
    Test client with the stateful mock patched in.
    Module-scoped so sequential tests share conversation/session state.
    """
    with patch(
        "routes.chat.get_or_create_ai_service",
        side_effect=e2e_mock_factory.get_or_create,
    ):
        yield TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _send_messages(client, user_id, session_number, count, conversation_id=None):
    """
    Send `count` chat messages for a session. Returns the list of responses
    and the conversation_id used.
    """
    responses = []
    for i in range(count):
        payload = {
            "message": f"Test message {i + 1} for session {session_number}",
            "user_id": user_id,
            "session_number": session_number,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        resp = client.post(CHAT_URL, json=payload)
        assert resp.status_code == 200, f"Chat failed: {resp.text}"
        data = resp.json()
        conversation_id = data["conversation_id"]
        responses.append(data)

    return responses, conversation_id


def _complete_session(client, user_id, session_number, conversation_id=None):
    """Send enough messages to complete a session. Returns responses and conv_id."""
    responses, conv_id = _send_messages(
        client, user_id, session_number, MESSAGES_PER_SESSION, conversation_id
    )

    # Last response should indicate session complete
    last = responses[-1]
    assert last.get("session_complete") is True, (
        f"Session {session_number} did not complete. "
        f"Last response: {last}"
    )
    return responses, conv_id


def _assert_session_completed(client, user_id, session_number):
    """Verify a session shows as completed in progress endpoint."""
    resp = client.get(f"{SESSION_PROGRESS_URL}/{user_id}")
    assert resp.status_code == 200
    progress = resp.json()

    completed = [
        p for p in progress
        if p["session_number"] == session_number and p["completed_at"] is not None
    ]
    assert len(completed) == 1, (
        f"Session {session_number} not found as completed. Progress: {progress}"
    )
    return progress


# ---------------------------------------------------------------------------
# Test 1: Onboarding
# ---------------------------------------------------------------------------


class TestE2EFullFlow:
    """Ordered E2E tests that build on each other."""

    def test_new_user_onboarding(self, e2e_client):
        """POST onboarding -> verify user status -> verify empty progress."""
        # Complete onboarding
        resp = e2e_client.post(
            ONBOARDING_URL,
            json={"user_id": E2E_USER_ID, "onboarding_completed": True},
        )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == E2E_USER_ID

        # Verify user status
        resp = e2e_client.get(f"{USER_STATUS_URL}/{E2E_USER_ID}")
        assert resp.status_code == 200
        status = resp.json()
        assert status["onboarding_completed"] is True
        assert status["user_id"] == E2E_USER_ID

        # Verify no sessions started yet
        resp = e2e_client.get(f"{SESSION_PROGRESS_URL}/{E2E_USER_ID}")
        assert resp.status_code == 200
        assert resp.json() == []

    # -------------------------------------------------------------------
    # Test 2-5: Sessions 1-4
    # -------------------------------------------------------------------

    def test_session_1_full_flow(self, e2e_client):
        """Complete session 1 and verify progress."""
        responses, conv_id = _complete_session(
            e2e_client, E2E_USER_ID, session_number=1
        )

        # Verify intermediate messages were not marked complete
        for r in responses[:-1]:
            assert r.get("session_complete") is not True

        # Verify progress shows session 1 completed
        progress = _assert_session_completed(e2e_client, E2E_USER_ID, 1)

        # Session 1 should be the only entry (created + completed by chat router)
        session_1 = [p for p in progress if p["session_number"] == 1]
        assert len(session_1) == 1
        assert session_1[0]["completed_at"] is not None

    def test_session_2_full_flow(self, e2e_client):
        """Complete session 2 and verify progress."""
        _complete_session(e2e_client, E2E_USER_ID, session_number=2)

        progress = _assert_session_completed(e2e_client, E2E_USER_ID, 2)

        # Both sessions 1 and 2 should be completed
        completed_sessions = [
            p["session_number"] for p in progress if p["completed_at"] is not None
        ]
        assert 1 in completed_sessions
        assert 2 in completed_sessions

    def test_session_3_full_flow(self, e2e_client):
        """Complete session 3 and verify progress."""
        _complete_session(e2e_client, E2E_USER_ID, session_number=3)
        _assert_session_completed(e2e_client, E2E_USER_ID, 3)

    def test_session_4_full_flow(self, e2e_client):
        """Complete session 4 and verify all sessions done."""
        _complete_session(e2e_client, E2E_USER_ID, session_number=4)

        # Verify ALL 4 sessions completed
        resp = e2e_client.get(f"{SESSION_PROGRESS_URL}/{E2E_USER_ID}")
        assert resp.status_code == 200
        progress = resp.json()

        completed_sessions = sorted(
            p["session_number"] for p in progress if p["completed_at"] is not None
        )
        assert completed_sessions == [1, 2, 3, 4], (
            f"Expected all 4 sessions completed, got: {completed_sessions}"
        )

    # -------------------------------------------------------------------
    # Test 6: Returning user
    # -------------------------------------------------------------------

    def test_returning_user(self, e2e_client):
        """After completing all sessions, verify returning user state."""
        # User status still shows onboarding completed
        resp = e2e_client.get(f"{USER_STATUS_URL}/{E2E_USER_ID}")
        assert resp.status_code == 200
        assert resp.json()["onboarding_completed"] is True

        # All 4 sessions still show completed
        resp = e2e_client.get(f"{SESSION_PROGRESS_URL}/{E2E_USER_ID}")
        assert resp.status_code == 200
        progress = resp.json()
        completed = sorted(
            p["session_number"] for p in progress if p["completed_at"] is not None
        )
        assert completed == [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# Test 7: Full program in a single test (independent of class tests above)
# ---------------------------------------------------------------------------


def test_full_program_sequential():
    """
    Run the entire flow in one test: onboarding -> session 1 -> 2 -> 3 -> 4.

    Uses a fresh user_id and fresh mock factory so it's fully independent.
    """
    user_id = f"e2e_sequential_{uuid.uuid4().hex[:8]}"
    factory = StatefulMockFactory(messages_per_session=MESSAGES_PER_SESSION)

    with patch(
        "routes.chat.get_or_create_ai_service",
        side_effect=factory.get_or_create,
    ):
        client = TestClient(app)

        # --- Onboarding ---
        resp = client.post(
            ONBOARDING_URL,
            json={"user_id": user_id, "onboarding_completed": True},
        )
        assert resp.status_code == 200

        resp = client.get(f"{USER_STATUS_URL}/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["onboarding_completed"] is True

        resp = client.get(f"{SESSION_PROGRESS_URL}/{user_id}")
        assert resp.status_code == 200
        assert resp.json() == []

        # --- Sessions 1 through 4 ---
        for session_num in range(1, 5):
            responses, conv_id = _complete_session(
                client, user_id, session_number=session_num
            )

            # Verify this session is now completed
            _assert_session_completed(client, user_id, session_num)

        # --- Final verification: all 4 sessions completed ---
        resp = client.get(f"{SESSION_PROGRESS_URL}/{user_id}")
        assert resp.status_code == 200
        progress = resp.json()

        completed = sorted(
            p["session_number"] for p in progress if p["completed_at"] is not None
        )
        assert completed == [1, 2, 3, 4], (
            f"Full program test: expected [1, 2, 3, 4], got {completed}"
        )

        # Returning user check
        resp = client.get(f"{USER_STATUS_URL}/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["onboarding_completed"] is True
