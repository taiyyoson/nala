"""
User Routes - API endpoints for onboarding status tracking

Provides endpoints to update and retrieve a user's onboarding completion state.
"""

import traceback

from authentication.auth_service import verify_token
from config.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from models.user import User
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(tags=["User"])


class OnboardingRequest(BaseModel):
    onboarding_completed: bool = False


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
