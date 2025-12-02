"""
Utility for parsing and storing goals across coaching sessions
"""
from typing import Dict, List, Optional, Any
import re


def is_goal_statement(text: str, min_words: int = 4) -> bool:
    """
    Check if text appears to be a goal statement
    
    Args:
        text: User input text
        min_words: Minimum word count for valid goal
    
    Returns:
        bool: True if text looks like a goal statement
    """
    text_lower = text.lower().strip()
    
    # Check if it's too short
    if len(text.split()) < min_words:
        return False
    
    # Check for non-goal phrases
    non_goal_phrases = [
        'no', 'yes', 'maybe', 'i dont know', "i don't know", 'not sure',
        'just want to stick', 'thats all', "that's all", 'nothing else',
        'im good', "i'm good", 'no more', 'nope', 'nah', 'keep it'
    ]
    
    if any(phrase in text_lower for phrase in non_goal_phrases):
        return False
    
    # Check if starts with non-goal words
    if text_lower.startswith(('no ', 'yes ', 'maybe ')):
        return False
    
    # Check if it's a question
    is_question = (
        '?' in text or 
        any(phrase in text_lower for phrase in ['how about', 'what if', 'maybe we', 'could we'])
    )
    
    if is_question:
        return False
    
    return True


def reword_goal_with_llm(goal_text: str, llm_client, context: Dict[str, Any] = None) -> str:
    """
    Use LLM to reword a messy goal into a clean, SMART format
    
    Args:
        goal_text: The original goal text (may be messy/conversational)
        llm_client: The LLM client or evaluator for API calls
        context: Optional context (discovery info, confidence level, etc.)
    
    Returns:
        str: Clean, professionally worded goal
    """
    if not llm_client:
        return goal_text
    
    # Build context string if provided
    context_str = ""
    if context:
        if context.get("confidence"):
            context_str += f"\nConfidence level: {context['confidence']}/10"
        if context.get("discovery"):
            discovery = context['discovery']
            if discovery.get("current_exercise"):
                context_str += f"\nCurrent exercise: {discovery['current_exercise']}"
            if discovery.get("current_sleep"):
                context_str += f"\nCurrent sleep: {discovery['current_sleep']}"
    
    prompt = f"""Rewrite this goal into a clear, concise, SMART format. Remove conversational filler and make it action-oriented.

Original goal: "{goal_text}"{context_str}

Requirements:
- Start with an action verb (e.g., "Walk", "Get", "Exercise", "Eat", "Complete")
- Be specific about what, when, and how often
- Keep it under 20 words
- Remove phrases like "I want to", "ok", "lets", "i can live with that", "maybe", "like"
- Make it clear and measurable
- If it mentions progression (like "increment by 10 mins"), include that

Return ONLY the reworded goal, nothing else."""

    try:
        # Check if it's an LLMEvaluator or direct Anthropic client
        if hasattr(llm_client, 'call_llm'):
            # It's an LLMEvaluator
            response = llm_client.call_llm(prompt, max_tokens=150)
            reworded = response.strip()
        elif hasattr(llm_client, 'messages'):
            # It's an Anthropic client
            response = llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            reworded = response.content[0].text.strip()
        else:
            # Unknown client type, return original
            print(f"[DEBUG] Unknown LLM client type: {type(llm_client)}")
            return goal_text
        
        # Remove quotes if LLM added them
        reworded = reworded.strip('"\'')
        
        # Ensure it's not too long
        if len(reworded.split()) <= 25 and reworded:
            return reworded
        else:
            # Fallback to original if too long or empty
            return goal_text
            
    except Exception as e:
        print(f"[DEBUG] Goal rewording failed: {e}")
        return goal_text


def extract_goal_from_text(text: str, goal_keywords: Optional[List[str]] = None) -> Optional[str]:
    """
    Extract a goal statement from user text
    
    Args:
        text: User input text
        goal_keywords: Optional list of keywords that indicate a goal statement
    
    Returns:
        str or None: Extracted goal text if found
    """
    if goal_keywords is None:
        goal_keywords = [
            "want to", "goal is", "goal:", "would like to", 
            "hoping to", "trying to", "plan to", "i want", "my goal"
        ]
    
    text_lower = text.lower()
    
    # Check if user is stating a goal
    has_goal_keyword = any(phrase in text_lower for phrase in goal_keywords)
    
    if has_goal_keyword and is_goal_statement(text):
        return text.strip()
    
    return None


def enhance_goal_with_details(base_goal: str, additional_text: str) -> str:
    """
    Combine a base goal with additional details
    
    Args:
        base_goal: The main goal statement
        additional_text: Additional specifics (timing, frequency, etc.)
    
    Returns:
        str: Enhanced goal statement
    """
    additional_lower = additional_text.lower()
    
    # Check for time/measurement indicators
    time_indicators = ['week', 'month', 'day', 'by', 'within', 'in']
    has_time = any(ind in additional_lower for ind in time_indicators)
    
    # Check for numbers
    has_numbers = bool(re.findall(r'\d+', additional_text))
    
    # Only enhance if additional text has specificity
    if has_time or has_numbers:
        return f"{base_goal} {additional_text}".strip()
    
    return additional_text.strip()


def store_goal(
    goal_text: str,
    existing_goals: List[Dict[str, Any]],
    confidence: Optional[int] = None,
    smart_analysis: Optional[Dict[str, Any]] = None,
    refinement_attempts: int = 0,
    session_number: int = 1,
    similarity_threshold: int = 50,
    llm_client = None,
    context: Dict[str, Any] = None
) -> bool:
    """
    Store a goal, avoiding duplicates and handling updates
    
    Args:
        goal_text: The goal statement to store
        existing_goals: List of existing goal dictionaries
        confidence: Confidence level (1-10)
        smart_analysis: SMART analysis results
        refinement_attempts: Number of refinement attempts
        session_number: Session where goal was created
        similarity_threshold: Character length to check for similarity
        llm_client: Optional LLM client for goal rewording
        context: Optional context for rewording (discovery, confidence, etc.)
    
    Returns:
        bool: True if goal was stored/updated, False if skipped
    """
    # Validate goal
    if not is_goal_statement(goal_text):
        return False
    
    # Reword goal if LLM client is provided
    if llm_client:
        goal_text = reword_goal_with_llm(goal_text, llm_client, context)
        print(f"[DEBUG] Goal reworded to: {goal_text}")
    
    # Check for duplicates or similar goals
    goal_prefix = goal_text[:similarity_threshold]
    
    for existing in existing_goals:
        existing_prefix = existing["goal"][:similarity_threshold]
        
        if existing_prefix == goal_prefix:
            # Update existing goal if new one is longer/better
            if len(goal_text) > len(existing["goal"]):
                existing["goal"] = goal_text
                existing["smart_analysis"] = smart_analysis
                existing["refinement_attempts"] = refinement_attempts
            
            # Update confidence if provided
            if confidence is not None:
                existing["confidence"] = confidence
            
            return True
    
    # Add new goal
    goal_entry = {
        "goal": goal_text,
        "confidence": confidence,
        "smart_analysis": smart_analysis,
        "refinement_attempts": refinement_attempts,
        "session_created": session_number,
        "status": "active"
    }
    
    existing_goals.append(goal_entry)
    return True


def format_goals_summary(goals: List[Dict[str, Any]]) -> str:
    """
    Format goals list into a readable summary
    
    Args:
        goals: List of goal dictionaries
    
    Returns:
        str: Formatted summary string
    """
    if not goals:
        return "No goals set yet."
    
    lines = []
    for i, goal_data in enumerate(goals, 1):
        goal = goal_data["goal"]
        confidence = goal_data.get("confidence")
        status = goal_data.get("status", "active")
        
        line = f"{i}. {goal}"
        if confidence:
            line += f" (Confidence: {confidence}/10)"
        if status != "active":
            line += f" [{status.upper()}]"
        
        lines.append(line)
    
    return "\n".join(lines)


def extract_refined_goal_from_coach_response(
    coach_response: str,
    user_input: str
) -> Optional[str]:
    """
    Extract a refined goal when coach is summarizing/confirming
    
    Args:
        coach_response: The coach's response text
        user_input: The user's input text
    
    Returns:
        str or None: Refined goal if detected
    """
    coach_lower = coach_response.lower()
    user_lower = user_input.lower()
    
    # Check if coach is summarizing
    refined_goal_indicators = [
        "so you're thinking",
        "okay, so",
        "perfect, so",
        "so your goal is",
        "that sounds like",
        "let me make sure i understand",
        "let me make sure i have",
        "your smart goal is",
        "your complete goal",
        "so monday",
        "so just to make sure"
    ]
    
    is_summarizing = any(indicator in coach_lower for indicator in refined_goal_indicators)
    
    if not is_summarizing:
        return None
    
    # Try to extract goal from coach's statement
    # Pattern 1: "your goal is: [GOAL]" or "your SMART goal is: [GOAL]"
    goal_statement_match = re.search(
        r'(?:your (?:complete )?(?:smart )?goal (?:is|right):)\s*(.+?)(?:\.|$)',
        coach_lower,
        re.IGNORECASE
    )
    
    if goal_statement_match:
        goal_text = goal_statement_match.group(1).strip()
        # Clean up and capitalize properly
        if goal_text:
            return goal_text.capitalize()
    
    # Pattern 2: Extract walking goals with specific format
    # "walk for X minutes, Y times a week"
    walk_match = re.search(
        r'walk(?:ing)? for (\d+) minutes?,\s*(\d+|three|two|four|five) times? (?:a|per) week',
        coach_lower
    )
    
    if walk_match:
        minutes = walk_match.group(1)
        frequency = walk_match.group(2)
        
        # Convert word numbers to digits
        word_to_num = {'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7'}
        if frequency.lower() in word_to_num:
            frequency = word_to_num[frequency.lower()]
        
        return f"Walk for {minutes} minutes, {frequency} times per week"
    
    # Pattern 3: Extract sleep goals
    hours_match = re.search(r'(\d+)\s*hours?', coach_lower)
    hours = hours_match.group(1) if hours_match else None
    
    freq_match = re.search(r'(\d+)\s*(times?|days?|nights?)\s*(per |a |this |each )?week', coach_lower)
    frequency = freq_match.group(1) if freq_match else None
    
    # Extract days mentioned
    days_mentioned = []
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    for day in day_names:
        if day in user_lower or day in coach_lower:
            days_mentioned.append(day.capitalize())
    
    # Remove duplicates while preserving order
    days_mentioned = list(dict.fromkeys(days_mentioned))
    
    # Construct refined goal
    if hours and (frequency or days_mentioned):
        if days_mentioned and len(days_mentioned) >= 2:
            if len(days_mentioned) == 2:
                days_str = f"{days_mentioned[0]} and {days_mentioned[1]}"
            else:
                days_str = ', '.join(days_mentioned[:-1]) + f", and {days_mentioned[-1]}"
            return f"Get {hours} hours of sleep on {days_str} each week"
        elif frequency:
            return f"Get {hours} hours of sleep {frequency} nights per week"
    
    return None


def check_coach_goal_acceptance(coach_response: str) -> bool:
    """
    Check if coach has accepted/confirmed the goal
    
    Args:
        coach_response: The coach's response text
    
    Returns:
        bool: True if coach accepted the goal
    """
    coach_response_lower = coach_response.lower()
    
    acceptance_patterns = [
        r"you've got a clear.*goal",
        r"that's a solid goal",
        r"solid starting point",
        r"fantastic.*goal",
        r"excellent.*goal", 
        r"perfect.*goal",
        r"great goal",
        r"this is going to",
        r"you're all set",
        r"how will you remind",
        r"how will you track",
        r"what.*remind yourself",
        r"on a scale.*confident"
    ]
    
    return any(re.search(pattern, coach_response_lower) for pattern in acceptance_patterns)