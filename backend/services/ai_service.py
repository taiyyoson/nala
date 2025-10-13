"""
AI Service - Bridge to AI Backend RAG System

This service handles communication with the AI-backend RAG chatbot system,
managing LLM selection, context retrieval, and response generation.
"""

from typing import List, Dict, Optional, Tuple, AsyncGenerator
import sys
import os

# Add AI-backend to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../AI-backend'))


class AIService:
    """
    Service for interacting with the RAG-based AI backend.

    Responsibilities:
    - Initialize and manage RAG chatbot instances
    - Generate responses using vector search + LLM
    - Handle streaming responses
    - Manage model selection and switching
    - Format conversation history for RAG system
    """

    def __init__(self, model: str = 'claude-sonnet-4', top_k: int = 3):
        """
        Initialize AI Service

        Args:
            model: LLM model to use (e.g., 'gpt-4o-mini', 'claude-sonnet-4')
            top_k: Number of similar coaching examples to retrieve
        """
        # TODO: Initialize RAG chatbot
        # from rag_dynamic import UnifiedRAGChatbot
        # self.chatbot = UnifiedRAGChatbot(model=model, top_k=top_k)
        pass

    async def generate_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[str] = None,
        use_history: bool = True
    ) -> Tuple[str, List[Dict], str]:
        """
        Generate a response using the RAG system.

        Args:
            message: User's input message
            conversation_history: Previous messages in format [{"role": "user/assistant", "content": "..."}]
            user_id: Optional user identifier for personalization
            use_history: Whether to include conversation history in context

        Returns:
            Tuple of (response_text, retrieved_sources, model_name)
        """
        # TODO: Implement response generation
        # 1. Format conversation history for RAG system
        # 2. Call chatbot.generate_response(message, use_history)
        # 3. Return structured response
        raise NotImplementedError("Response generation not yet implemented")

    async def stream_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response token-by-token (for real-time chat experience).

        Args:
            message: User's input message
            conversation_history: Previous messages
            user_id: Optional user identifier

        Yields:
            Response chunks as they're generated
        """
        # TODO: Implement streaming response
        # Note: May need to modify RAG system to support streaming
        raise NotImplementedError("Streaming not yet implemented")
        yield  # Make this a generator

    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different LLM model.

        Args:
            model_name: Name of model to switch to

        Returns:
            True if successful, False otherwise
        """
        # TODO: Implement model switching
        # self.chatbot.switch_model(model_name)
        raise NotImplementedError("Model switching not yet implemented")

    def get_available_models(self) -> List[Dict[str, str]]:
        """
        Get list of available LLM models.

        Returns:
            List of dicts with model info: [{"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"}]
        """
        # TODO: Return available models from RAG system
        # return [{"id": k, **v} for k, v in UnifiedRAGChatbot.AVAILABLE_MODELS.items()]
        raise NotImplementedError("Model listing not yet implemented")

    def reset_conversation(self):
        """Clear conversation history in the RAG system."""
        # TODO: Implement conversation reset
        # self.chatbot.reset_conversation()
        pass
