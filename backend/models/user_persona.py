"""
User Persona Model - Database model for the participant's coaching profile

Stores persona attributes from the onboarding questionnaire (focus areas,
communication style, barriers) and what the coach learns across sessions.
"""

from datetime import datetime

from models.base import Base
from sqlalchemy import JSON, Column, DateTime, String

FOCUS_AREAS = [
    "nutrition",
    "physical_activity",
    "sleep_rest",
    "stress_management",
    "hydration",
    "self_care",
]

COMMUNICATION_STYLES = ["encouraging", "direct", "structured"]


class UserPersona(Base):
    """
    User persona database model. One row per user.

    Attributes:
        user_id: Primary key (Firebase uid, same as users.id)
        focus_areas: Health areas the user wants to work on (keys from FOCUS_AREAS)
        communication_style: Preferred coaching style (key from COMMUNICATION_STYLES)
        barriers: [{"text": str, "source": "onboarding" | int session number}]
        personal_context: [{"text": str, "session": int}] - routines, interests, life events
        strategies: [{"text": str, "session": int}] - what has worked for them
        goal_history: [{"goal": str, "confidence": int, "session": int, "outcome": str}]
        stress_history: [{"session": int, "level": int}]
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "user_personas"

    user_id = Column(String, primary_key=True, index=True)

    # Set by onboarding questionnaire
    focus_areas = Column(JSON, default=list)
    communication_style = Column(String, nullable=True)
    barriers = Column(JSON, default=list)

    # Added by end-of-session updates
    personal_context = Column(JSON, default=list)
    strategies = Column(JSON, default=list)
    goal_history = Column(JSON, default=list)
    stress_history = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserPersona(user_id={self.user_id}, style={self.communication_style})>"

    def to_dict(self):
        """Convert the persona to a dictionary for API responses."""
        return {
            "user_id": self.user_id,
            "has_profile": True,
            "focus_areas": self.focus_areas or [],
            "communication_style": self.communication_style,
            "barriers": self.barriers or [],
            "personal_context": self.personal_context or [],
            "strategies": self.strategies or [],
            "goal_history": self.goal_history or [],
            "stress_history": self.stress_history or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def empty_dict(user_id: str):
        """Default profile returned when a user has not saved one yet."""
        return {
            "user_id": user_id,
            "has_profile": False,
            "focus_areas": [],
            "communication_style": None,
            "barriers": [],
            "personal_context": [],
            "strategies": [],
            "goal_history": [],
            "stress_history": [],
            "created_at": None,
            "updated_at": None,
        }
