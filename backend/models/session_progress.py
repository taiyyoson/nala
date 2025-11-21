from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

from models.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

Base = declarative_base()

class SessionProgress(Base):
    __tablename__ = "session_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    session_number = Column(Integer, nullable=False)

    unlocked_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

def mark_complete(self, unlock_delay_days: int = 7):
    """
    Mark this session as completed (only once), and calculate the unlock time
    for the next session. NOTE: Does NOT create or modify next session here;
    that happens in the router.
    def to_dict(self):
        """Convert session progress into a JSON-serializable dict."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_number": self.session_number,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "unlocked_at": (self.unlocked_at.isoformat() if self.unlocked_at else None),
        }

    Args:
        unlock_delay_days (int): Days after completion the next session unlocks.
                                 Default: 7

    Returns:
        datetime: The timestamp when the *next* session should unlock.
    """
    now = datetime.utcnow()

    # Only set completed_at once — don't overwrite if already done
    if not self.completed_at:
        self.completed_at = now

    # The next session unlocks AFTER unlock_delay_days (usually 7)
    unlock_time = now + timedelta(days=unlock_delay_days)

    return unlock_time


def to_dict(self):
    """
    Convert this SessionProgress object to a dictionary for JSON/response.
    Useful for returning data to frontend.

    Returns:
        dict: JSON serializable session progress data.
    """
    return {
        "id": self.id,
        "user_id": self.user_id,
        "session_number": self.session_number,
        "unlocked_at": (
            self.unlocked_at.isoformat() if self.unlocked_at else None
        ),
        "completed_at": (
            self.completed_at.isoformat() if self.completed_at else None
        ),
        "created_at": (
            self.created_at.isoformat() if hasattr(self, "created_at") and self.created_at else None
        ),
        "updated_at": (
            self.updated_at.isoformat() if hasattr(self, "updated_at") and self.updated_at else None
        ),
    }
