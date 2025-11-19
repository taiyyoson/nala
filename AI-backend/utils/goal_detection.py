"""
Utilities for detecting goals in user input.
"""


def is_likely_goal(text: str, min_words: int = 4) -> bool:
    """
    Check if text is likely a goal statement.
    
    Args:
        text: User's input
        min_words: Minimum word count to be considered a goal
        
    Returns:
        True if likely a goal statement
    """
    text_lower = text.lower().strip()
    
    # Phrases that indicate NOT a goal
    non_goal_phrases = [
        'no', 'yes', 'maybe', 'i dont know', "i don't know", 'not sure',
        'just want to stick', 'thats all', "that's all", 'nothing else',
        'im good', "i'm good", 'no more', 'nope', 'nah'
    ]
    
    # Check for non-goals
    if any(phrase in text_lower for phrase in non_goal_phrases):
        return False
    
    # Too short
    if len(text.split()) < min_words:
        return False
    
    # Starts with affirmation
    if text_lower.startswith(('no ', 'yes ', 'maybe ')):
        return False
    
    # Check for situation vs goal
    situation_phrases = ['i have', 'i am', "i'm", 'my life', 'my schedule']
    is_situation = any(phrase in text_lower for phrase in situation_phrases)
    
    if is_situation and 'want' not in text_lower and 'goal' not in text_lower and 'like to' not in text_lower:
        return False
    
    return True


def contains_goal_keywords(text: str) -> bool:
    """
    Check if text contains goal-related keywords.
    
    Args:
        text: User input text
        
    Returns:
        True if contains goal keywords
    """
    text_lower = text.lower()
    goal_keywords = [
        "want to", "goal is", "goal:", "would like to", "hoping to", 
        "trying to", "plan to", "i want", "my goal"
    ]
    return any(phrase in text_lower for phrase in goal_keywords)


def is_goal_question(text: str) -> bool:
    """
    Check if text is a question about a goal rather than a goal statement.
    
    Args:
        text: User input text
        
    Returns:
        True if it's a question
    """
    question_indicators = ['?', 'how about', 'what if', 'maybe', 'would', 'could', 'should']
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in question_indicators) or text.endswith('?')


def is_too_short_for_goal(text: str, min_words: int = 4) -> bool:
    """
    Check if text is too short to be a meaningful goal.
    
    Args:
        text: User input text
        min_words: Minimum word count
        
    Returns:
        True if too short
    """
    return len(text.split()) < min_words