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
def mark_session_complete(user_id: str, session_number: int, db: Session = Depends(get_db)):
    progress = (
        db.query(SessionProgress)
        .filter_by(user_id=user_id, session_number=session_number)
        .first()
    )

    if not progress:
        progress = SessionProgress(user_id=user_id, session_number=session_number)
        db.add(progress)

    # Step 1: mark session complete
    unlock_time_for_next = progress.mark_complete(unlock_delay_days=7)

    # Step 2: Unlock the next session
    next_session_number = session_number + 1
    next_session_progress = None

    if next_session_number <= 4:
        next_session_progress = (
            db.query(SessionProgress)
            .filter_by(user_id=user_id, session_number=next_session_number)
            .first()
        )

        if not next_session_progress:
            next_session_progress = SessionProgress(
                user_id=user_id,
                session_number=next_session_number,
                unlocked_at=unlock_time_for_next
            )
            db.add(next_session_progress)
        elif not next_session_progress.unlocked_at:
            next_session_progress.unlocked_at = unlock_time_for_next

    db.commit()
    db.refresh(progress)
    if next_session_progress:
        db.refresh(next_session_progress)

    return {
        "message": "Session marked complete",
        "completed_session": progress.to_dict(),
        "next_session": next_session_progress.to_dict() if next_session_progress else None,
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

