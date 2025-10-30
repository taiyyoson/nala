"""
Request Adapter - Transform API Requests to Service Format

Converts FastAPI request models to formats expected by service layer and RAG system.
"""

from typing import Dict, List, Optional


class RequestAdapter:
    """
    Adapter for transforming incoming API requests.

    Responsibilities:
    - Convert FastAPI ChatRequest -> AIService input format
    - Format conversation history for RAG system
    - Extract and validate request parameters
    - Handle different request types (message, stream, etc.)
    """

    @staticmethod
    def chat_request_to_ai_input(
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Transform API chat request to AI service input format.

        Args:
            message: User's message text
            conversation_id: Optional conversation ID
            user_id: Optional user ID
            conversation_history: List of previous messages

        Returns:
            Dict formatted for AIService.generate_response():
            {
                "message": str,
                "conversation_history": [{"role": "user/assistant", "content": "..."}],
                "user_id": str,
                "use_history": bool
            }
        """
        # Validate message
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        # Format conversation history
        formatted_history = RequestAdapter.format_conversation_history(
            conversation_history or []
        )

        # Determine if we should use history
        use_history = len(formatted_history) > 0

        return {
            "message": message.strip(),
            "conversation_history": formatted_history,
            "user_id": user_id,
            "use_history": use_history,
        }

    @staticmethod
    def format_conversation_history(messages: List[Dict]) -> List[Dict[str, str]]:
        """
        Format conversation messages for RAG system.

        The RAG system expects: [{"role": "user/assistant", "content": "..."}]
        API messages may have additional fields (timestamp, message_id, metadata, etc.)

        Args:
            messages: List of message dicts from database or API

        Returns:
            Formatted message list for RAG system
        """
        formatted = []

        for msg in messages:
            # Extract only role and content
            role = msg.get("role")
            content = msg.get("content")

            # Validate
            if not role or not content:
                continue

            # Only include user and assistant messages (skip system)
            if role in ["user", "assistant"]:
                formatted.append({"role": role, "content": content})

        return formatted

    @staticmethod
    def validate_message_content(message: str) -> bool:
        """
        Validate user message content.

        Args:
            message: Message text to validate

        Returns:
            True if valid

        Raises:
            ValueError: If message is invalid
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        if len(message) > 5000:
            raise ValueError("Message too long (max 5000 characters)")

        return True

    @staticmethod
    def extract_model_preference(
        request_metadata: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Extract model preference from request metadata.

        Args:
            request_metadata: Optional metadata dict from request

        Returns:
            Model name if specified, None otherwise
        """
        if not request_metadata:
            return None

        return request_metadata.get("model_preference") or request_metadata.get("model")
