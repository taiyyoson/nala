"""
User Routes - API endpoints for onboarding status tracking

Provides endpoints to update and retrieve a user’s onboarding completion state.
"""

from config.database import get_db
from fastapi import APIRouter, Depends
from models.user import User
from sqlalchemy.orm import Session

router = APIRouter(tags=["User"])


@router.post("/onboarding")
def update_onboarding_status(payload: dict, db: Session = Depends(get_db)):
    """
    Mark the user’s onboarding as completed or update their onboarding state.

    Request Body:
        user_id (str): Unique user identifier
        onboarding_completed (bool): Completion flag (default: False)
    """
    user_id = payload.get("user_id")
    onboarding_completed = payload.get("onboarding_completed", False)

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


@router.get("/status/{user_id}")
def get_user_status(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieve onboarding completion status for a given user.

    Path Parameter:
        user_id (str): Unique user identifier

    Returns:
        dict: { "onboarding_completed": bool }
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"onboarding_completed": False}

    return {
        "user_id": user.id,
        "onboarding_completed": user.onboarding_completed,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }
