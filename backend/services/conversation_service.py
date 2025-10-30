"""
Conversation Service - Conversation State Management

This service manages conversation lifecycle, message history, and metadata.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from services.database_service import DatabaseService


class ConversationService:
    """
    Service for managing conversations and message history.

    Responsibilities:
    - Create and manage conversations
    - Add messages to conversations
    - Retrieve conversation history
    - Handle conversation metadata (title, created_at, etc.)
    - Manage user-conversation relationships
    """

    def __init__(self, database_service: DatabaseService):
        """
        Initialize Conversation Service

        Args:
            database_service: DatabaseService instance for persistence
        """
        self.db = database_service

    async def create_conversation(
        self,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Create a new conversation.

        Args:
            user_id: ID of the user starting the conversation
            title: Optional title for the conversation
            metadata: Optional metadata (week_number, session_type, etc.)

        Returns:
            Dict with conversation data:
            {
                "conversation_id": str,
                "user_id": str,
                "title": str,
                "created_at": datetime,
                "updated_at": datetime,
                "message_count": int
            }
        """
        conversation_data = {
            "user_id": user_id,
            "title": title or "New Conversation",
            "metadata": metadata or {},
        }

        conversation = self.db.create_conversation(conversation_data)

        return conversation.to_dict()

    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Retrieve a conversation by ID.

        Args:
            conversation_id: ID of conversation to retrieve

        Returns:
            Conversation data with messages, or None if not found
            {
                "conversation_id": str,
                "user_id": str,
                "title": str,
                "message_count": int,
                "messages": [...],
                "created_at": datetime,
                "updated_at": datetime
            }
        """
        conversation = self.db.get_conversation_by_id(conversation_id)

        if not conversation:
            return None

        # Get messages
        messages = self.db.get_messages_by_conversation(conversation_id)

        # Convert to dict
        conv_dict = conversation.to_dict()
        conv_dict["messages"] = [msg.to_api_format() for msg in messages]

        return conv_dict

    async def list_conversations(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict]:
        """
        List conversations for a user.

        Args:
            user_id: User ID to filter by
            limit: Maximum number of conversations to return
            offset: Pagination offset

        Returns:
            List of conversation summaries
        """
        conversations = self.db.list_user_conversations(user_id, limit, offset)

        # Convert to dicts and add preview of last message
        result = []
        for conv in conversations:
            conv_dict = conv.to_dict()

            # Get last message for preview
            recent_messages = self.db.get_recent_messages(conv.id, limit=1)
            if recent_messages:
                last_msg = recent_messages[0]
                conv_dict["last_message_preview"] = last_msg.content[:100]
                if len(last_msg.content) > 100:
                    conv_dict["last_message_preview"] += "..."
            else:
                conv_dict["last_message_preview"] = None

            result.append(conv_dict)

        return result

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Add a message to a conversation.

        Args:
            conversation_id: ID of conversation
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Optional metadata (model used, sources, etc.)

        Returns:
            Message data:
            {
                "message_id": str,
                "conversation_id": str,
                "role": str,
                "content": str,
                "metadata": dict,
                "timestamp": datetime
            }
        """
        # Validate conversation exists
        conversation = self.db.get_conversation_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Create message
        message_data = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }

        message = self.db.create_message(message_data)

        # Auto-generate title from first user message if needed
        if not conversation.title or conversation.title == "New Conversation":
            if role == "user" and conversation.message_count == 1:
                conversation.generate_title_from_first_message(self.db.session)
                self.db.session.commit()

        return message.to_dict()

    async def get_conversation_history(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for AI service.

        Args:
            conversation_id: ID of conversation
            limit: Optional limit on number of messages (most recent)

        Returns:
            List of messages in format for RAG system:
            [{"role": "user/assistant", "content": "..."}]
        """
        messages = self.db.get_messages_by_conversation(conversation_id, limit=limit)

        # Format for AI service
        history = []
        for msg in messages:
            history.append({"role": msg.role, "content": msg.content})

        return history

    async def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """
        Update conversation title.

        Args:
            conversation_id: ID of conversation
            title: New title

        Returns:
            True if successful
        """
        conversation = self.db.update_conversation(conversation_id, {"title": title})
        return conversation is not None

    async def update_conversation_metadata(
        self, conversation_id: str, metadata: Dict
    ) -> bool:
        """
        Update conversation metadata.

        Args:
            conversation_id: ID of conversation
            metadata: New metadata dict

        Returns:
            True if successful
        """
        conversation = self.db.update_conversation(
            conversation_id, {"metadata": metadata}
        )
        return conversation is not None

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: ID of conversation to delete

        Returns:
            True if successful
        """
        return self.db.delete_conversation(conversation_id)

    async def get_or_create_conversation(
        self, conversation_id: Optional[str], user_id: Optional[str]
    ) -> str:
        """
        Get existing conversation or create a new one.

        Args:
            conversation_id: Optional conversation ID
            user_id: User ID

        Returns:
            Conversation ID
        """
        # If conversation_id provided, verify it exists
        if conversation_id:
            conversation = self.db.get_conversation_by_id(conversation_id)
            if conversation:
                return conversation_id

        # Create new conversation
        new_conv = await self.create_conversation(user_id=user_id)
        return new_conv["conversation_id"]
