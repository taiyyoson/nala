"""
Utilities for saving and loading session data.
Extracted from Session1Manager and Session2Manager.
"""
import json
from datetime import datetime
from typing import Dict, Any, List


def save_session_data(
    state_value: str,
    session_data: Dict[str, Any],
    conversation_history: List[Dict[str, str]] = None,
    filename: str = None,
    session_prefix: str = "session"
) -> str:
    """
    Save session data to JSON file.
    
    Args:
        state_value: Current state as string (e.g., state.value)
        session_data: Dictionary of session data
        conversation_history: List of conversation messages
        filename: Optional filename, auto-generated if None
        session_prefix: Prefix for filename (e.g., "session1", "session2")
        
    Returns:
        The filename that was saved to
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_prefix}_{timestamp}.json"
    
    # Prepare data for JSON serialization
    session_data_copy = session_data.copy()
    
    # Convert sets to lists if present
    if "questions_asked" in session_data_copy and isinstance(session_data_copy["questions_asked"], set):
        session_data_copy["questions_asked"] = list(session_data_copy["questions_asked"])
    
    # Build the complete data structure
    data = {
        "state": state_value,
        "session_data": session_data_copy,
        "conversation_history": conversation_history or []
    }
    
    # Write to file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename


def load_session_data(filename: str) -> Dict[str, Any]:
    """
    Load session data from JSON file.
    
    Args:
        filename: Path to JSON file
        
    Returns:
        Dictionary containing:
            - state: State value as string
            - session_data: Session data dictionary
            - conversation_history: List of messages
    """
    with open(filename, 'r') as f:
        data = json.load(f)
    
    # Convert lists back to sets if needed
    if "session_data" in data:
        session_data = data["session_data"]
        if "questions_asked" in session_data and isinstance(session_data["questions_asked"], list):
            session_data["questions_asked"] = set(session_data["questions_asked"])
    
    return {
        "state": data.get("state"),
        "session_data": data.get("session_data", {}),
        "conversation_history": data.get("conversation_history", [])
    }


def load_session1_data_for_session2(filename: str) -> Dict[str, Any]:
    """
    Load Session 1 data specifically for use in Session 2.
    Extracts just the relevant information.
    
    Args:
        filename: Path to Session 1 JSON file
        
    Returns:
        Dictionary with Session 1 data formatted for Session 2:
            - user_name
            - goal_details
            - discovery (if available)
    """
    try:
        data = load_session_data(filename)
        session_data = data.get("session_data", {})
        
        return {
            "user_name": session_data.get("user_name"),
            "goal_details": session_data.get("goal_details", []),
            "discovery": session_data.get("discovery", {})
        }
    except Exception as e:
        print(f"Error loading Session 1 data: {e}")
        return None