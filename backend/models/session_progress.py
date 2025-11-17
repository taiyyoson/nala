"""
SessionProgress Model - Tracks each user's session completion and unlock timing.

Stores:
- session_number: 1–4
- completed_at: when the user finished a session
- unlocked_at: when the session becomes available
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from models.base import Base


class SessionProgress(Base):
    __tablename__ = "session_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    session_number = Column(Integer)
    completed_at = Column(DateTime, nullable=True)
    unlocked_at = Column(DateTime, nullable=True, default=None)

    def mark_complete(self):
        """Mark this session as complete and set next unlock time (+7 days)."""
        self.completed_at = datetime.utcnow()
        self.unlocked_at = self.completed_at + timedelta(days=7)

    def to_dict(self):
        """Convert session progress into a JSON-serializable dict."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_number": self.session_number,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "unlocked_at": (
                self.unlocked_at.isoformat() if self.unlocked_at else None
            ),
        }

    def __repr__(self):
        return (
            f"<SessionProgress(user_id={self.user_id}, "
            f"session={self.session_number}, completed_at={self.completed_at}, "
            f"unlocked_at={self.unlocked_at})>"
        )
