"""
Response Adapter - Transform Service Responses to API Format

Converts service layer and RAG system outputs to FastAPI response models.
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime


class ResponseAdapter:
    """
    Adapter for transforming service responses to API format.

    Responsibilities:
    - Convert RAG output -> FastAPI ChatResponse
    - Format retrieved sources for API response
    - Add metadata (model used, retrieval info, etc.)
    - Handle error responses
    """

    @staticmethod
    def ai_response_to_chat_response(
        rag_output: Tuple[str, List[Dict], str],
        conversation_id: str,
        message_id: Optional[str] = None
    ) -> Dict:
        """
        Transform RAG output to ChatResponse format.

        Args:
            rag_output: Tuple from AIService.generate_response()
                       (response_text, retrieved_sources, model_name)
            conversation_id: ID of the conversation
            message_id: Optional message ID (generated if not provided)

        Returns:
            Dict matching ChatResponse model:
            {
                "response": str,
                "conversation_id": str,
                "message_id": str,
                "timestamp": datetime,
                "metadata": {
                    "model": str,
                    "sources": list,
                    "source_count": int
                }
            }
        """
        # TODO: Implement transformation
        # 1. Unpack RAG output tuple
        # 2. Generate message ID if needed
        # 3. Format sources metadata
        # 4. Build response dict
        raise NotImplementedError("Response transformation not yet implemented")

    @staticmethod
    def format_sources(retrieved_sources: List[Dict]) -> List[Dict]:
        """
        Format retrieved coaching examples for API response.

        Args:
            retrieved_sources: Raw sources from vector search

        Returns:
            Formatted sources with relevant fields:
            [
                {
                    "similarity": float,
                    "category": str,
                    "goal_type": str,
                    "example_snippet": str (truncated)
                }
            ]
        """
        # TODO: Implement source formatting
        # 1. Extract relevant fields
        # 2. Truncate long text
        # 3. Add similarity scores
        # 4. Remove sensitive info if any
        raise NotImplementedError("Source formatting not yet implemented")

    @staticmethod
    def conversation_to_api_format(
        conversation_data: Dict,
        messages: List[Dict]
    ) -> Dict:
        """
        Format conversation data for API response.

        Args:
            conversation_data: Conversation metadata from database
            messages: List of messages in conversation

        Returns:
            Formatted conversation dict:
            {
                "conversation_id": str,
                "title": str,
                "created_at": datetime,
                "updated_at": datetime,
                "message_count": int,
                "messages": [...]
            }
        """
        # TODO: Implement conversation formatting
        # 1. Combine conversation metadata with messages
        # 2. Format timestamps
        # 3. Add computed fields (message_count, etc.)
        raise NotImplementedError("Conversation formatting not yet implemented")

    @staticmethod
    def format_conversation_summary(conversation_data: Dict) -> Dict:
        """
        Format conversation summary for list view (without full messages).

        Args:
            conversation_data: Conversation metadata

        Returns:
            Summary dict:
            {
                "conversation_id": str,
                "title": str,
                "last_message_preview": str,
                "message_count": int,
                "updated_at": datetime
            }
        """
        # TODO: Implement summary formatting
        # Used for conversation list endpoint
        raise NotImplementedError("Summary formatting not yet implemented")

    @staticmethod
    def error_to_api_response(error: Exception, status_code: int = 500) -> Dict:
        """
        Format error as API response.

        Args:
            error: Exception that occurred
            status_code: HTTP status code

        Returns:
            Error response dict:
            {
                "error": str,
                "message": str,
                "status_code": int,
                "timestamp": datetime
            }
        """
        # TODO: Implement error formatting
        # 1. Extract error message
        # 2. Add timestamp
        # 3. Include status code
        # 4. Don't leak sensitive info
        raise NotImplementedError("Error formatting not yet implemented")

    @staticmethod
    def streaming_chunk_to_sse(chunk: str, done: bool = False) -> str:
        """
        Format response chunk for Server-Sent Events (SSE).

        Args:
            chunk: Text chunk to send
            done: Whether this is the final chunk

        Returns:
            SSE-formatted string: "data: {json}\n\n"
        """
        # TODO: Implement SSE formatting
        # Used for streaming responses
        raise NotImplementedError("SSE formatting not yet implemented")
