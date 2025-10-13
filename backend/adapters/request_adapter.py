"""
Request Adapter - Transform API Requests to Service Format

Converts FastAPI request models to formats expected by service layer and RAG system.
"""

from typing import List, Dict, Optional


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
        conversation_history: Optional[List[Dict]] = None
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
        # TODO: Implement transformation logic
        # 1. Validate message content
        # 2. Format conversation history
        # 3. Determine if history should be used
        # 4. Return structured dict
        raise NotImplementedError("Request transformation not yet implemented")

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
        # TODO: Implement history formatting
        # 1. Extract only role and content
        # 2. Ensure role is "user" or "assistant"
        # 3. Filter out system messages if any
        # 4. Maintain chronological order
        raise NotImplementedError("History formatting not yet implemented")

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
        # TODO: Implement validation
        # 1. Check not empty
        # 2. Check length limits
        # 3. Check for prohibited content
        raise NotImplementedError("Message validation not yet implemented")

    @staticmethod
    def extract_model_preference(
        request_metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Extract model preference from request metadata.

        Args:
            request_metadata: Optional metadata dict from request

        Returns:
            Model name if specified, None otherwise
        """
        # TODO: Implement model extraction
        # Allow users to specify preferred LLM in request
        raise NotImplementedError("Model extraction not yet implemented")
