"""
RAG Service - Minimal integration with AI-backend RAG system

This is a simplified version for the sprint. When merging with the full
architecture branch, this will be replaced by the complete ai_service.py
with proper initialization, error handling, and streaming support.
"""

import sys
from pathlib import Path
from typing import Tuple, List, Dict, Optional

# Add AI-backend to path
ai_backend_path = Path(__file__).parent.parent.parent / "AI-backend"
sys.path.insert(0, str(ai_backend_path))

from rag_dynamic import UnifiedRAGChatbot

# Singleton RAG chatbot instance
_rag_chatbot: Optional[UnifiedRAGChatbot] = None


def get_rag_chatbot(model: str = "claude-sonnet-4", top_k: int = 3) -> UnifiedRAGChatbot:
    """Get or create the RAG chatbot singleton instance."""
    global _rag_chatbot
    if _rag_chatbot is None:
        _rag_chatbot = UnifiedRAGChatbot(model=model, top_k=top_k)
    return _rag_chatbot


def get_rag_response(
    message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, List[Dict]]:
    """
    Get response from RAG system.

    Args:
        message: User's message
        conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]

    Returns:
        Tuple of (response_text, retrieved_sources)
    """
    chatbot = get_rag_chatbot()

    # Update conversation history if provided
    if conversation_history:
        # Convert to format expected by RAG chatbot
        chatbot.conversation_history = conversation_history

    # Generate response
    response, sources, model = chatbot.generate_response(message, use_history=True)

    return response, sources
