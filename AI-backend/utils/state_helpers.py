"""
Helper utilities for state transitions.
"""
from typing import Dict, Any, Optional
import re


def create_state_result(next_state=None, context: str = "", trigger_rag: bool = True) -> Dict[str, Any]:
    """
    Create a standardized state transition result.
    
    Args:
        next_state: Next state to transition to (or None)
        context: Context string for the coach
        trigger_rag: Whether to trigger RAG retrieval
        
    Returns:
        Dictionary with state transition info
    """
    return {
        "next_state": next_state,
        "context": context,
        "trigger_rag": trigger_rag
    }


def check_affirmative(text: str) -> bool:
    """
    Check if text is affirmative (yes, yeah, etc.).
    
    Args:
        text: User input text
        
    Returns:
        True if affirmative
    """
    text_lower = text.lower().strip()
    affirmative_words = ["yes", "yeah", "yep", "sure", "yup", "ok", "okay", "i do", "i have"]
    return any(word in text_lower for word in affirmative_words)


def check_negative(text: str) -> bool:
    """
    Check if text is negative (no, nope, etc.).
    
    Args:
        text: User input text
        
    Returns:
        True if negative
    """
    text_lower = text.lower().strip()
    negative_words = ["no", "nope", "nah", "not really", "don't", "dont", "no questions"]
    return any(word in text_lower for word in negative_words)


def extract_number(text: str) -> Optional[int]:
    """
    Extract first number from text (useful for stress/confidence ratings).
    
    Args:
        text: User input text
        
    Returns:
        First number found or None
    """
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(numbers[0])
    return None


def check_wants_more(text: str) -> bool:
    """Check if user wants to add more (goals, questions, etc.)"""
    text_lower = text.lower().strip()
    more_keywords = ["yes", "yeah", "another", "more", "add", "one more", "i'd like", "i want"]
    return any(word in text_lower for word in more_keywords)


def check_done(text: str) -> bool:
    """Check if user is done (no more goals, questions, etc.)"""
    text_lower = text.lower().strip()
    done_keywords = ["no", "nope", "just", "only", "focus on", "stick with", "that's all", "thats all", "done", "good"]
    return any(word in text_lower for word in done_keywords)