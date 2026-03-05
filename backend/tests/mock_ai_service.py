"""
Stateful Mock AI Service for E2E Testing

Simulates session state progression deterministically:
- Tracks call count per instance
- Advances to "end_session" state after a configurable number of messages
- Returns predictable responses for each session
- Supports save_session() as a no-op

Used by E2E tests to verify the full user flow without real LLM calls.
"""

from unittest.mock import MagicMock


class StatefulMockAIService:
    """
    A mock AI service that simulates session state progression.

    After `messages_until_end` calls to generate_response(), the session
    manager state transitions to "end_session", triggering session completion
    logic in the chat router.
    """

    def __init__(self, session_number: int = 1, messages_until_end: int = 3):
        self.session_number = session_number
        self.messages_until_end = messages_until_end
        self.call_count = 0
        self._state_value = "active"

        # Set up chatbot mock matching the real AIService interface
        self.chatbot = MagicMock()
        self.chatbot.session_manager = MagicMock()
        self.chatbot.session_manager.get_state = MagicMock(
            side_effect=self._get_state
        )
        self.chatbot.save_session = MagicMock()
        self.chatbot.conversation_history = []

    def _get_state(self):
        """Return a mock state object with the current state value."""
        mock_state = MagicMock()
        mock_state.value = self._state_value
        return mock_state

    async def generate_response(
        self,
        message: str,
        conversation_history=None,
        user_id=None,
        use_history: bool = True,
    ):
        """
        Generate a deterministic response and advance state.

        Returns (response, sources, model_name) matching AIService interface.
        """
        self.call_count += 1

        if self.call_count >= self.messages_until_end:
            self._state_value = "end_session"
            response = (
                f"Great work! We've completed session {self.session_number}. "
                "I look forward to our next conversation!"
            )
        else:
            response = (
                f"Session {self.session_number}, message {self.call_count}: "
                "Let's continue working on your health goals."
            )

        return (response, [], "mock-model")

    @property
    def is_complete(self):
        return self._state_value == "end_session"


class StatefulMockFactory:
    """
    Factory that creates and caches StatefulMockAIService instances per conversation.

    Mimics the real _ai_service_cache behavior: returns the same service instance
    for repeated calls with the same conversation_id.
    """

    def __init__(self, messages_per_session: int = 3):
        self._services = {}
        self.messages_per_session = messages_per_session

    def get_or_create(
        self,
        conversation_id: str,
        session_number: int = None,
        user_id: str = None,
    ):
        """Return existing or create new StatefulMockAIService for a conversation."""
        if conversation_id not in self._services:
            service = StatefulMockAIService(
                session_number=session_number or 1,
                messages_until_end=self.messages_per_session,
            )
            self._services[conversation_id] = service
        return self._services[conversation_id]

    def reset(self):
        """Clear all cached services."""
        self._services.clear()
