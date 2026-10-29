"""
User Routes - API endpoints for onboarding status and persona profile

Provides endpoints to update and retrieve a user's onboarding completion state
and their persona profile (focus areas, communication style, barriers).
"""

import traceback
from typing import List, Literal, Optional

from authentication.auth_service import verify_token
from config.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from models.user import User
from models.user_persona import FOCUS_AREAS, UserPersona
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

router = APIRouter(tags=["User"])

MAX_BARRIERS = 10
MAX_BARRIER_LENGTH = 200


class OnboardingRequest(BaseModel):
    onboarding_completed: bool = False


class ProfileRequest(BaseModel):
    focus_areas: List[str] = Field(default_factory=list)
    communication_style: Optional[Literal["encouraging", "direct", "structured"]] = None
    barriers: List[str] = Field(default_factory=list, max_length=MAX_BARRIERS)

    @field_validator("focus_areas")
    @classmethod
    def check_focus_areas(cls, value):
        invalid = [area for area in value if area not in FOCUS_AREAS]
        if invalid:
            raise ValueError(f"Unknown focus areas: {invalid}. Allowed: {FOCUS_AREAS}")
        return list(dict.fromkeys(value))  # drop duplicates, keep order

    @field_validator("barriers")
    @classmethod
    def check_barriers(cls, value):
        cleaned = []
        for barrier in value:
            barrier = barrier.strip()
            if len(barrier) > MAX_BARRIER_LENGTH:
                raise ValueError(f"Barriers must be {MAX_BARRIER_LENGTH} characters or fewer")
            if barrier and barrier.lower() not in [b.lower() for b in cleaned]:
                cleaned.append(barrier)
        return cleaned


@router.post("/onboarding")
def update_onboarding_status(
    payload: OnboardingRequest,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    Mark the user's onboarding as completed or update their onboarding state.
    """
    try:
        user_id = decoded_token["uid"]
        onboarding_completed = payload.onboarding_completed

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            # Create new user record if not found
            user = User(id=user_id, onboarding_completed=onboarding_completed)
            db.add(user)
        else:
            # Update existing record
            user.onboarding_completed = onboarding_completed

        db.commit()
        return {"message": "Onboarding status updated", "user_id": user.id}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/{user_id}")
def get_user_status(
    user_id: str,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    Retrieve onboarding completion status for a given user.
    """
    try:
        auth_user_id = decoded_token["uid"]

        user = db.query(User).filter(User.id == auth_user_id).first()

        if not user:
            # User authenticated via Firebase but no DB row yet — create one
            user = User(id=auth_user_id, onboarding_completed=False)
            db.add(user)
            db.commit()

        return {
            "user_id": user.id,
            "onboarding_completed": user.onboarding_completed,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profile")
def get_user_profile(
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    Retrieve the authenticated user's persona profile.
    Returns empty defaults (has_profile: false) if none has been saved yet.
    """
    try:
        user_id = decoded_token["uid"]
        persona = db.query(UserPersona).filter(UserPersona.user_id == user_id).first()

        if not persona:
            return UserPersona.empty_dict(user_id)

        return persona.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/profile")
def update_user_profile(
    payload: ProfileRequest,
    decoded_token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    Save the onboarding questionnaire answers to the user's persona profile.

    Barriers from onboarding are replaced; barriers learned in sessions are kept.
    Session-learned fields (personal_context, strategies, goal_history,
    stress_history) are not editable here.
    """
    try:
        user_id = decoded_token["uid"]
        persona = db.query(UserPersona).filter(UserPersona.user_id == user_id).first()

        if not persona:
            persona = UserPersona(user_id=user_id)
            db.add(persona)

        session_barriers = [
            b for b in (persona.barriers or []) if b.get("source") != "onboarding"
        ]
        onboarding_barriers = [
            {"text": text, "source": "onboarding"} for text in payload.barriers
        ]

        persona.focus_areas = payload.focus_areas
        persona.communication_style = payload.communication_style
        persona.barriers = onboarding_barriers + session_barriers

        db.commit()
        db.refresh(persona)
        return persona.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")
