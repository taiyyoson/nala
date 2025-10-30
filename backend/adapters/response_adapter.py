"""
Response Adapter - Transform Service Responses to API Format

Converts service layer and RAG system outputs to FastAPI response models.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple


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
        message_id: Optional[str] = None,
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
        response_text, sources, model_name = rag_output

        # Generate message ID if not provided
        if not message_id:
            message_id = f"msg_{uuid.uuid4().hex[:12]}"

        # Format sources
        formatted_sources = ResponseAdapter.format_sources(sources)

        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "timestamp": datetime.utcnow(),
            "metadata": {
                "model": model_name,
                "sources": formatted_sources,
                "source_count": len(sources),
            },
        }

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
        formatted = []

        for source in retrieved_sources:
            formatted_source = {
                "similarity": round(source.get("similarity", 0.0), 3),
                "category": source.get("category"),
                "goal_type": source.get("goal_type"),
            }

            # Add truncated snippet of participant response
            participant_resp = source.get("participant_response", "")
            if participant_resp:
                snippet = participant_resp[:100]
                if len(participant_resp) > 100:
                    snippet += "..."
                formatted_source["example_snippet"] = snippet

            formatted.append(formatted_source)

        return formatted

    @staticmethod
    def conversation_to_api_format(
        conversation_data: Dict, messages: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Format conversation data for API response.

        Args:
            conversation_data: Conversation metadata from database
            messages: Optional list of messages in conversation

        Returns:
            Formatted conversation dict:
            {
                "conversation_id": str,
                "title": str,
                "created_at": datetime,
                "updated_at": datetime,
                "message_count": int,
                "messages": [...] (if provided)
            }
        """
        result = {
            "conversation_id": conversation_data.get("conversation_id"),
            "title": conversation_data.get("title"),
            "user_id": conversation_data.get("user_id"),
            "message_count": conversation_data.get("message_count", 0),
            "created_at": conversation_data.get("created_at"),
            "updated_at": conversation_data.get("updated_at"),
            "metadata": conversation_data.get("metadata", {}),
        }

        if messages is not None:
            result["messages"] = messages

        return result

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
        return {
            "conversation_id": conversation_data.get("conversation_id"),
            "title": conversation_data.get("title"),
            "last_message_preview": conversation_data.get("last_message_preview"),
            "message_count": conversation_data.get("message_count", 0),
            "created_at": conversation_data.get("created_at"),
            "updated_at": conversation_data.get("updated_at"),
        }

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
        return {
            "error": type(error).__name__,
            "message": str(error),
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
        }

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
        import json

        data = {"content": chunk, "done": done}

        return f"data: {json.dumps(data)}\n\n"
