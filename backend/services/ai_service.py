"""
AI Service - Bridge to AI Backend RAG System

This service handles communication with the AI-backend RAG chatbot system,
managing LLM selection, context retrieval, and response generation.
"""

import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import openai
from config.settings import settings

openai.api_key = settings.openai_api_key

ai_backend_path = Path(__file__).parent.parent.parent / "AI-backend"
sys.path.insert(0, str(ai_backend_path))

from query import VectorSearch
from rag_dynamic import UnifiedRAGChatbot
from session1_manager import SessionBasedRAGChatbot
from session2_manager import Session2RAGChatbot
from session3_manager import Session3RAGChatbot
from session4_manager import Session4RAGChatbot


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

    def __init__(
        self,
        model: str = "claude-sonnet-4.5",
        top_k: int = 3,
        session_number: Optional[int] = None,
        previous_session_data: Optional[Dict] = None,
        user_id: Optional[str] = None,
    ):
        """
        Initialize AI Service

        Args:
            model: LLM model to use (e.g., 'gpt-4o-mini', 'claude-sonnet-4')
            top_k: Number of similar coaching examples to retrieve
            session_number: Session number (1-4) for structured coaching, None for general chat
            previous_session_data: Data from previous session (for sessions 2+)
            user_id: User ID for session persistence
        """
        self.model = model
        self.top_k = top_k
        self.session_number = session_number
        self.user_id = user_id


        match session_number:
            case 1:
                # Session 1: Goal setting and introduction
                self.chatbot = SessionBasedRAGChatbot(model=model, top_k=top_k, uid=user_id)
                print(
                    f"✓ AIService initialized with Session 1 structured flow (model: {model}, uid: {user_id})"
                )
            case 2:
                # Session 2: Progress review and goal adjustment
                self.chatbot = Session2RAGChatbot(
                    session1_data=previous_session_data,
                    model=model,
                    top_k=top_k
                )
                print(
                    f"✓ AIService initialized with Session 2 structured flow (model: {model})"
                )
            case 3:
                # Session 3: Continued progress and goal refinement
                self.chatbot = Session3RAGChatbot(
                    user_profile=previous_session_data,
                    model=model,
                    top_k=top_k
                )
                print(
                    f"✓ AIService initialized with Session 3 structured flow (model: {model})"
                )
            case 4:
                # Session 4: Final check-in and long-term planning
                self.chatbot = Session4RAGChatbot(
                    session3_data=previous_session_data,
                    model=model,
                    top_k=top_k
                )
                print(
                    f"✓ AIService initialized with Session 4 structured flow (model: {model})"
                )
            case _:
                # Default: General chat without session structure
                self.chatbot = UnifiedRAGChatbot(model=model, top_k=top_k)
                print(f"✓ AIService initialized with model: {model}, top_k: {top_k}")

    async def generate_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[str] = None,
        use_history: bool = True,
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

        if self.session_number not in [1, 2, 3, 4]:
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
            user_message=message, use_history=use_history
        )

        return (response, sources, model_name)

    async def stream_response(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[str] = None,
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

        response, sources, model = await self.generate_response(
            message, conversation_history, user_id
        )


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
            models.append(
                {"id": model_id, "name": info["name"], "provider": info["provider"]}
            )
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
