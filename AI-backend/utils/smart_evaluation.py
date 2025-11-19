"""
Utilities for SMART goal evaluation.
Extracted from Session1Manager and Session2Manager.
"""
import re
import json
from typing import Dict, Any
from .constants import TIME_WORDS, DAYS_OF_WEEK, ACTION_VERBS, ACTIVITY_NAMES, VAGUE_WORDS, GOAL_FILLER_PHRASES


def evaluate_smart_goal_with_llm(goal: str, llm_client) -> Dict[str, Any]:
    """
    Use LLM to evaluate if a goal is SMART.
    
    Args:
        goal: The goal text to evaluate
        llm_client: LLM client with evaluate_goal() method
        
    Returns:
        Dict with:
            - is_smart: bool
            - analysis: dict with criteria details
            - suggestions: str
            - missing_criteria: list of str
    """
    evaluation_prompt = f"""Evaluate if this goal is SMART (Specific, Measurable, Achievable, Relevant, Time-bound).

Goal: "{goal}"

STRICT CRITERIA:
- Specific: Must have a clear, detailed action (not vague like "eat better" or "exercise more")
- Measurable: Must include numbers, frequency, or quantifiable metrics (e.g., "30 minutes", "3 times", "2000 calories")
- Achievable: Should be realistic for a typical person
- Relevant: Related to health/wellness
- Time-bound: Must specify when/how often (e.g., "daily", "3x per week", "by Friday", "for 2 weeks")

Respond ONLY with a JSON object in this exact format:
{{
    "specific": {{"met": true/false, "issue": "reason if not met"}},
    "measurable": {{"met": true/false, "issue": "reason if not met"}},
    "achievable": {{"met": true/false, "issue": "reason if not met"}},
    "relevant": {{"met": true/false, "issue": "reason if not met"}},
    "timebound": {{"met": true/false, "issue": "reason if not met"}},
    "suggestions": "specific suggestions to make it SMART"
}}"""

    try:
        response = llm_client.evaluate_goal(evaluation_prompt)
        response = response.strip()
        
        # Clean up response
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        analysis = json.loads(response)
        
        # Check if all criteria are met
        is_smart = all(
            analysis[criterion]["met"] 
            for criterion in ["specific", "measurable", "achievable", "relevant", "timebound"]
        )
        
        # Build list of missing criteria
        missing = [
            criterion.upper() 
            for criterion in ["specific", "measurable", "achievable", "relevant", "timebound"]
            if not analysis[criterion]["met"]
        ]
        
        return {
            'is_smart': is_smart,
            'analysis': analysis,
            'suggestions': analysis.get('suggestions', ''),
            'missing_criteria': missing
        }
        
    except Exception as e:
        # Fall back to heuristic check if LLM fails
        return heuristic_smart_check(goal)


def heuristic_smart_check(goal: str) -> Dict[str, Any]:
    """
    Simple heuristic-based SMART check as fallback.
    Used when LLM is unavailable or fails.
    
    Args:
        goal: The goal text to evaluate
        
    Returns:
        Dict with same structure as evaluate_smart_goal_with_llm
    """
    goal_lower = goal.lower()
    
    # Check for numbers
    has_numbers = bool(re.search(r'\d+', goal))
    
    # Check for timeframe words (using constants)
    has_timeframe = any(word in goal_lower for word in TIME_WORDS)
    
    # Check for action verbs or activity names (using constants)
    has_action = (
        any(verb in goal_lower for verb in ACTION_VERBS) or 
        any(activity in goal_lower for activity in ACTIVITY_NAMES)
    )
    
    # Check for vague words (using constants)
    has_vague = any(word in goal_lower for word in VAGUE_WORDS) and not has_numbers
    
    # Check for specific days (using constants)
    has_specific_days = any(day in goal_lower for day in DAYS_OF_WEEK)
    
    # Determine if SMART
    is_smart = (
        has_numbers and 
        (has_timeframe or has_specific_days) and 
        has_action and 
        not has_vague and 
        len(goal.split()) >= 5
    )
    
    # Build missing criteria list
    missing = []
    if not has_action or has_vague: 
        missing.append("SPECIFIC")
    if not has_numbers: 
        missing.append("MEASURABLE")
    if not (has_timeframe or has_specific_days): 
        missing.append("TIMEBOUND")
    
    return {
        'is_smart': is_smart,
        'analysis': {
            'specific': {
                'met': has_action and not has_vague, 
                'issue': 'Use specific action verbs or activity names, avoid vague words'
            },
            'measurable': {
                'met': has_numbers, 
                'issue': 'Include specific numbers or quantities'
            },
            'achievable': {
                'met': True, 
                'issue': ''
            },
            'relevant': {
                'met': True, 
                'issue': ''
            },
            'timebound': {
                'met': has_timeframe or has_specific_days, 
                'issue': 'Specify frequency or deadline'
            }
        },
        'suggestions': 'Make it more specific with numbers and a clear timeframe',
        'missing_criteria': missing
    }


def create_concise_goal(full_goal: str) -> str:
    """
    Create a concise version of the goal for storage.
    Removes filler words and cleans up spacing.
    
    Args:
        full_goal: The full goal statement
        
    Returns:
        Concise version of the goal
    """
    concise = full_goal.lower()
    
    # Remove filler phrases (using constants)
    for phrase in GOAL_FILLER_PHRASES:
        concise = concise.replace(phrase, "")
    
    # Clean up spacing
    concise = " ".join(concise.split())
    
    # Capitalize first letter
    if concise:
        concise = concise[0].upper() + concise[1:]
    
    return concise.strip()