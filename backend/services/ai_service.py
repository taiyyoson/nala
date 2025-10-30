"""
AI Service - Bridge to AI Backend RAG System

This service handles communication with the AI-backend RAG chatbot system,
managing LLM selection, context retrieval, and response generation.
"""

from typing import List, Dict, Optional, Tuple, AsyncGenerator
import sys
import os
from pathlib import Path

# Add AI-backend to Python path
ai_backend_path = Path(__file__).parent.parent.parent / "AI-backend"
sys.path.insert(0, str(ai_backend_path))

# Import RAG system
from rag_dynamic import UnifiedRAGChatbot
from session1_manager import SessionBasedRAGChatbot
from query import VectorSearch


class AIService:
    """
    Service for interacting with the RAG-based AI backend.

    Responsibilities:
    - Initialize and manage RAG chatbot instances (with session management)
    - Generate responses using vector search + LLM
    - Handle streaming responses
    - Manage model selection and switching
    - Manage session state and transitions
    - Format conversation history for RAG system
    """

    def __init__(self, model: str = 'claude-sonnet-4', top_k: int = 3, session_number: Optional[int] = None):
        """
        Initialize AI Service

        Args:
            model: LLM model to use (e.g., 'gpt-4o-mini', 'claude-sonnet-4')
            top_k: Number of similar coaching examples to retrieve
            session_number: Session number (1-4) for structured coaching, None for general chat
        """
        self.model = model
        self.top_k = top_k
        self.session_number = session_number

        # Initialize appropriate chatbot based on session
        match session_number:
            case 1:
                # Session 1: Goal setting and introduction
                self.chatbot = SessionBasedRAGChatbot(model=model, top_k=top_k)
                print(f"✓ AIService initialized with Session 1 structured flow (model: {model})")
            case 2 | 3 | 4:
                # Future sessions - placeholder for now
                self.chatbot = UnifiedRAGChatbot(model=model, top_k=top_k)
                print(f"✓ AIService initialized for Session {session_number} (using base RAG, model: {model})")
            case _:
                # Default: General chat without session structure
                self.chatbot = UnifiedRAGChatbot(model=model, top_k=top_k)
                print(f"✓ AIService initialized with model: {model}, top_k: {top_k}")

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
        # Set conversation history in RAG chatbot
        if conversation_history and use_history:
            self.chatbot.conversation_history = conversation_history
        else:
            self.chatbot.conversation_history = []

        # Generate response using RAG system
        # This internally:
        # 1. Does vector search for similar coaching examples
        # 2. Builds context from retrieved examples
        # 3. Calls LLM API with context
        # 4. Returns (response, sources, model_name)
        response, sources, model_name = self.chatbot.generate_response(
            user_message=message,
            use_history=use_history
        )

        return (response, sources, model_name)

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

        Note: This is a placeholder. The current RAG system doesn't support streaming.
              For MVP, we generate the full response and yield it word-by-word.
        """
        # Generate full response
        response, sources, model = await self.generate_response(
            message, conversation_history, user_id
        )

        # Simulate streaming by yielding words
        words = response.split()
        for i, word in enumerate(words):
            yield word + " "

        # TODO: Implement true streaming when RAG system supports it
        # This would require modifying rag_dynamic.py to support streaming APIs

    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different LLM model.

        Args:
            model_name: Name of model to switch to
                       (e.g., 'gpt-4o', 'claude-sonnet-4', 'claude-opus-4')

        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.chatbot.switch_model(model_name)
            if success:
                self.model = model_name
                print(f"✓ Switched to model: {model_name}")
            return success
        except Exception as e:
            print(f"✗ Failed to switch model: {e}")
            return False

    def get_available_models(self) -> List[Dict[str, str]]:
        """
        Get list of available LLM models.

        Returns:
            List of dicts with model info:
            [
                {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
                {"id": "claude-sonnet-4", "name": "Claude Sonnet 4", "provider": "anthropic"}
            ]
        """
        models = []
        for model_id, info in UnifiedRAGChatbot.AVAILABLE_MODELS.items():
            models.append({
                "id": model_id,
                "name": info["name"],
                "provider": info["provider"]
            })
        return models

    def reset_conversation(self):
        """Clear conversation history in the RAG system."""
        self.chatbot.reset_conversation()
        print("✓ Conversation history cleared")

    def get_current_model(self) -> str:
        """Get currently active model name."""
        return self.model

    def test_vector_search(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Test vector search functionality (for debugging).

        Args:
            query: Test query
            limit: Number of results

        Returns:
            List of retrieved coaching examples
        """
        try:
            results = self.chatbot.retrieve(query, min_similarity=0.4)
            print(f"✓ Vector search test successful: {len(results)} results")
            return results
        except Exception as e:
            print(f"✗ Vector search test failed: {e}")
            return []
