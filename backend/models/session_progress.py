from datetime import datetime, timedelta

from models.base import Base
from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base


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
        """
        now = datetime.utcnow()

        if not self.completed_at:
            self.completed_at = now

        self.unlocked_at = now + timedelta(days=unlock_delay_days)
        return self.unlocked_at

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
            "unlocked_at": (self.unlocked_at.isoformat() if self.unlocked_at else None),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if hasattr(self, "created_at") and self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if hasattr(self, "updated_at") and self.updated_at
                else None
            ),
        }
