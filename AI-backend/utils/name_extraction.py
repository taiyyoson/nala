"""
Utility for extracting names from user input.
"""
from typing import Optional


def extract_name_from_text(text: str) -> Optional[str]:
    """
    Extract a name from user text.
    
    Args:
        text: User's message
        
    Returns:
        Extracted name or None
    """
    text_lower = text.lower().strip()
    
    # Check for "I'm", "my name is", etc.
    if any(word in text_lower for word in ["i'm", "im", "my name is", "call me", "i am"]):
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in ["i'm", "im", "name", "call", "i", "am"]:
                if i + 1 < len(words):
                    potential_name = words[i + 1].strip('.,!?')
                    if potential_name.lower() not in ["is", "a", "the", "and", "but", "so"]:
                        return potential_name
    
    # Check if it's just a short name response
    if len(text.split()) <= 3 and len(text) < 30:
        cleaned_name = text.strip('.,!?').strip()
        if cleaned_name and not any(word in text_lower for word in ["hello", "hi", "hey", "good", "morning", "afternoon"]):
            return cleaned_name
    
    return None