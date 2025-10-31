from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class UserBase(BaseModel):
    id: str
    email: str
    display_name: Optional[str]


class UserProfile(BaseModel):
    user_id: str
    onboarding_completed: bool = False
    preferred_name: Optional[str]
    timezone: Optional[str]
    notification_preferences: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
