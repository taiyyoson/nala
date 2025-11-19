"""
Helpers for discovery phase questions.
"""
from typing import List, Optional


# Discovery question order
DISCOVERY_QUESTIONS = [
    "general_about",
    "current_exercise", 
    "current_sleep",
    "current_eating",
    "free_time"
]

# Prompts for each discovery question
DISCOVERY_PROMPTS = {
    "general_about": "Tell me a bit about yourself - what's important to you right now?",
    "current_exercise": "What does your current exercise routine look like?",
    "current_sleep": "How are your sleep habits? How many hours do you typically get per night?",
    "current_eating": "What are your current eating habits like? Walk me through a typical day.",
    "free_time": "What do you like to do in your free time?"
}


def get_next_discovery_question(questions_asked: List[str]) -> Optional[str]:
    """
    Get the next discovery question to ask.
    
    Args:
        questions_asked: List of question keys already asked
        
    Returns:
        Next question key or None if all done
    """
    for question in DISCOVERY_QUESTIONS:
        if question not in questions_asked:
            return question
    return None


def get_discovery_prompt(question_key: str) -> str:
    """
    Get the prompt text for a discovery question.
    
    Args:
        question_key: Key like "current_exercise"
        
    Returns:
        Prompt text
    """
    return DISCOVERY_PROMPTS.get(question_key, "")


def is_discovery_complete(questions_asked: List[str], min_required: int = 3) -> bool:
    """
    Check if enough discovery questions have been asked.
    
    Args:
        questions_asked: List of questions already asked
        min_required: Minimum number of questions needed
        
    Returns:
        True if discovery phase is complete
    """
    return len(questions_asked) >= min_required


def get_remaining_questions(questions_asked: List[str]) -> List[str]:
    """
    Get list of questions that haven't been asked yet.
    
    Args:
        questions_asked: List of questions already asked
        
    Returns:
        List of remaining question keys
    """
    return [q for q in DISCOVERY_QUESTIONS if q not in questions_asked]