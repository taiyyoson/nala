"""
Session Routes - Manage session progress and unlock timing.

Provides endpoints to:
- Mark a session as completed
- Retrieve a user's session progress
- Get/save session conversation data (goals, user profile, etc.)
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from models.session_progress import SessionProgress
from sqlalchemy.orm import Session

# Add AI-backend to path for session database utilities
_ai_backend_path = Path(__file__).parent.parent.parent / "AI-backend"
if str(_ai_backend_path) not in sys.path:
    sys.path.insert(0, str(_ai_backend_path))

from utils.database import (
    load_session_from_db,
    get_latest_session_for_user,
    list_users,
)

router = APIRouter(prefix="/session", tags=["Session"])


@router.post("/complete")
def mark_session_complete(
    user_id: str, session_number: int, db: Session = Depends(get_db)
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


# ============================================================================
# Session Data Endpoints (for cross-session persistence)
# ============================================================================


@router.get("/data/{user_id}/{session_number}")
def get_session_data(user_id: str, session_number: int):
    """
    Get saved session data (user profile, goals, chat history) for a specific session.

    Args:
        user_id (str): Firebase UID of the user
        session_number (int): Session number (1–4)

    Returns:
        dict: Session data containing user_profile, session_info, chat_history
              or 404 if not found
    """
    data = load_session_from_db(user_id, session_number)

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for user {user_id}, session {session_number}",
        )

    return {
        "user_id": user_id,
        "session_number": session_number,
        "user_profile": data.get("user_profile", {}),
        "session_info": data.get("session_info", {}),
        "chat_history": data.get("chat_history", []),
    }


@router.get("/latest/{user_id}")
def get_latest_session(user_id: str):
    """
    Get the most recent session data for a user.

    Useful for determining:
    - What session the user should start next
    - Loading the most recent user profile data

    Args:
        user_id (str): Firebase UID of the user

    Returns:
        dict: Latest session data with session_number, or 404 if no sessions exist
    """
    data = get_latest_session_for_user(user_id)

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No sessions found for user {user_id}",
        )

    return {
        "user_id": user_id,
        "latest_session_number": data.get("session_number"),
        "next_session_number": min(data.get("session_number", 0) + 1, 4),
        "user_profile": data.get("user_profile", {}),
        "session_info": data.get("session_info", {}),
    }


@router.get("/users")
def get_all_users():
    """
    List all users who have session data in the database.

    Returns:
        list: List of users with uid, name, last_session, last_updated
    """
    users = list_users()
    return {"users": users, "total": len(users)}
