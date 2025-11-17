"""
Session Routes - Manage session progress and unlock timing.

Provides endpoints to:
- Mark a session as completed
- Retrieve a user's session progress
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from config.database import get_db
from models.session_progress import SessionProgress

router = APIRouter(prefix="/session", tags=["Session"])


@router.post("/complete")
def mark_session_complete(
    user_id: str,
    session_number: int,
    db: Session = Depends(get_db)
):
    """
    Mark a user's session as complete and set unlock time for next session.

    Args:
        user_id (str): Firebase UID of the user
        session_number (int): Session number (1–4)

    Returns:
        dict: SessionProgress record
    """
    progress = (
        db.query(SessionProgress)
        .filter_by(user_id=user_id, session_number=session_number)
        .first()
    )

    if not progress:
        # Create a new record if this session hasn't been tracked yet
        progress = SessionProgress(
            user_id=user_id,
            session_number=session_number
        )
        db.add(progress)

    # Mark completion + set unlock time
    progress.mark_complete()
    db.commit()
    db.refresh(progress)

    print(f"✅ Session {session_number} marked complete for user {user_id}")
    return {
        "message": "Session marked complete",
        "data": progress.to_dict()
    }


@router.get("/progress/{user_id}")
def get_user_progress(user_id: str, db: Session = Depends(get_db)):
    """
    Get all session progress records for a given user.
    Returns an empty list if none exist yet.
    """
    progress_list = (
        db.query(SessionProgress)
        .filter_by(user_id=user_id)
        .order_by(SessionProgress.session_number)
        .all()
    )

    # ✅ Return an empty list instead of raising 404
    if not progress_list:
        return []

    return [p.to_dict() for p in progress_list]

