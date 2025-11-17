"""
User Model - Database model for onboarding state tracking

Stores user identifiers and onboarding completion flag.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from models.base import Base


class User(Base):
    """
    User database model.

    Attributes:
        id: Primary key (UUID string)
        onboarding_completed: Indicates if onboarding flow is complete
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, onboarding_completed={self.onboarding_completed})>"

    def to_dict(self):
        """Convert the user object to a dictionary for API responses."""
        return {
            "user_id": self.id,
            "onboarding_completed": self.onboarding_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
