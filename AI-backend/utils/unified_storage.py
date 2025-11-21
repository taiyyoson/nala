"""
Unified session storage with consistent JSON structure across all sessions.
Replaces utils/session_storage.py
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


def save_unified_session(
    uid: str,
    user_name: str,
    session_number: int,
    current_state: str,
    discovery: Dict[str, Optional[str]],
    goals: List[Dict[str, Any]],
    session_metadata: Dict[str, Any],
    conversation_history: List[Dict[str, str]] = None,
    filename: str = None
) -> str:
    """
    Save session data in unified format.
    
    Args:
        uid: User ID
        user_name: User's name
        session_number: Which session (1, 2, 3, 4)
        current_state: Current state of the session
        discovery: Discovery questions and answers
        goals: List of all goals with confidence and stress
        session_metadata: Session-specific data (state info, etc.)
        conversation_history: Chat messages
        filename: Optional filename
        
    Returns:
        Filename that was saved
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user_{uid}_session{session_number}_{timestamp}.json"
    
    # Build unified structure
    unified_data = {
        "user_profile": {
            "uid": uid,
            "name": user_name,
            "discovery_questions": {
                "tell_me_about_yourself": discovery.get("general_about"),
                "exercise_routine": discovery.get("current_exercise"),
                "sleep_habits": discovery.get("current_sleep"),
                "eating_habits": discovery.get("current_eating"),
                "free_time": discovery.get("free_time_activities")
            },
            "goals": goals  # List of {goal, confidence, stress, session_created, status}
        },
        "session_info": {
            "session_number": session_number,
            "current_state": current_state,
            "timestamp": datetime.now().isoformat(),
            "metadata": session_metadata
        },
        "chat_history": conversation_history or []
    }
    
    # Write to file
    with open(filename, 'w') as f:
        json.dump(unified_data, f, indent=2)
    
    return filename


def load_unified_session(filename: str) -> Dict[str, Any]:
    """
    Load unified session data.
    
    Args:
        filename: Path to JSON file
        
    Returns:
        Dictionary with unified structure
    """
    with open(filename, 'r') as f:
        return json.load(f)


def extract_user_profile(filename: str) -> Dict[str, Any]:
    """
    Extract just the user profile (for passing to next session).
    
    Args:
        filename: Path to session JSON file
        
    Returns:
        User profile dict with uid, name, discovery, goals
    """
    data = load_unified_session(filename)
    return data.get("user_profile", {})


def get_active_goals(goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get only active (not completed/dropped) goals.
    
    Args:
        goals: List of all goals
        
    Returns:
        List of active goals
    """
    return [g for g in goals if g.get("status") != "completed" and g.get("status") != "dropped"]


def add_goal_to_profile(
    goals: List[Dict[str, Any]],
    goal_text: str,
    confidence: int,
    stress: Optional[int] = None,
    session_number: int = 1
) -> List[Dict[str, Any]]:
    """
    Add a new goal to the goals list.
    
    Args:
        goals: Existing goals list
        goal_text: The goal statement
        confidence: Confidence level (1-10)
        stress: Stress level (1-10) if applicable
        session_number: Which session this was created in
        
    Returns:
        Updated goals list
    """
    new_goal = {
        "goal": goal_text,
        "confidence": confidence,
        "stress": stress,
        "session_created": session_number,
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    goals.append(new_goal)
    return goals


def update_goal_status(
    goals: List[Dict[str, Any]],
    goal_text: str,
    new_status: str,
    new_confidence: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Update a goal's status (active, completed, dropped, modified).
    
    Args:
        goals: Goals list
        goal_text: The goal to update
        new_status: New status
        new_confidence: Updated confidence if changed
        
    Returns:
        Updated goals list
    """
    for goal in goals:
        if goal["goal"] == goal_text:
            goal["status"] = new_status
            if new_confidence is not None:
                goal["confidence"] = new_confidence
            goal["updated_at"] = datetime.now().isoformat()
            break
    return goals


# Migration helpers for existing session managers

def convert_session1_to_unified(session1_data: Dict[str, Any], uid: str = None) -> Dict[str, Any]:
    """
    Convert Session 1 format to unified format.
    
    Args:
        session1_data: Old session1 session_data dict
        uid: User ID (generate if not provided)
        
    Returns:
        Unified format dict
    """
    if uid is None:
        uid = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Extract discovery
    discovery_old = session1_data.get("discovery", {})
    discovery = {
        "general_about": discovery_old.get("general_about"),
        "current_exercise": discovery_old.get("current_exercise"),
        "current_sleep": discovery_old.get("current_sleep"),
        "current_eating": discovery_old.get("current_eating"),
        "free_time_activities": discovery_old.get("free_time_activities")
    }
    
    # Convert goals
    goals = []
    for goal_detail in session1_data.get("goal_details", []):
        goals.append({
            "goal": goal_detail.get("goal"),
            "confidence": goal_detail.get("confidence"),
            "stress": None,  # Session 1 doesn't track stress
            "session_created": 1,
            "status": "active",
            "created_at": session1_data.get("session_start")
        })
    
    return {
        "uid": uid,
        "user_name": session1_data.get("user_name"),
        "discovery": discovery,
        "goals": goals,
        "session_metadata": {
            "turn_count": session1_data.get("turn_count"),
            "current_goal": session1_data.get("current_goal")
        }
    }


def convert_session2_to_unified(session2_data: Dict[str, Any], uid: str = None) -> Dict[str, Any]:
    """
    Convert Session 2 format to unified format.
    
    Args:
        session2_data: Old session2 session_data dict
        uid: User ID (generate if not provided)
        
    Returns:
        Unified format dict
    """
    if uid is None:
        uid = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Get discovery from previous goals if available
    discovery = {}
    if session2_data.get("previous_goals"):
        # Discovery might be in previous session data
        discovery = {}
    
    # Combine previous goals and new goals
    goals = []
    
    # Previous goals (from Session 1)
    for prev_goal in session2_data.get("previous_goals", []):
        goals.append({
            "goal": prev_goal.get("goal"),
            "confidence": prev_goal.get("confidence"),
            "stress": session2_data.get("stress_level"),
            "session_created": 1,
            "status": "active",  # Determine based on path_chosen
            "created_at": None
        })
    
    # New goals from Session 2
    for new_goal in session2_data.get("new_goals", []):
        goals.append({
            "goal": new_goal,
            "confidence": session2_data.get("confidence_level"),
            "stress": session2_data.get("stress_level"),
            "session_created": 2,
            "status": "active",
            "created_at": session2_data.get("session_start")
        })
    
    return {
        "uid": uid,
        "user_name": session2_data.get("user_name"),
        "discovery": discovery,
        "goals": goals,
        "session_metadata": {
            "turn_count": session2_data.get("turn_count"),
            "stress_level": session2_data.get("stress_level"),
            "path_chosen": session2_data.get("path_chosen")
        }
    }