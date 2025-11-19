"""
Utility functions for session managers.
"""

from .smart_evaluation import (
    evaluate_smart_goal_with_llm,
    heuristic_smart_check,
    create_concise_goal
)

from .session_storage import (
    save_session_data,
    load_session_data,
    load_session1_data_for_session2
)

from .state_prompts import (
    get_session1_prompt,
    get_session2_prompt
)

from .program_loader import load_program_info

from .name_extraction import extract_name_from_text

from .state_helpers import (
    create_state_result,
    check_affirmative,
    check_negative,
    extract_number,
    check_wants_more,
    check_done
)

from .discovery_helpers import (
    get_next_discovery_question,
    get_discovery_prompt,
    is_discovery_complete,
    get_remaining_questions,
    DISCOVERY_QUESTIONS,
    DISCOVERY_PROMPTS
)

from .goal_detection import (
    is_likely_goal,
    contains_goal_keywords,
    is_goal_question,
    is_too_short_for_goal
)

from .constants import (
    TIME_WORDS,
    DAYS_OF_WEEK,
    ACTION_VERBS,
    ACTIVITY_NAMES,
    VAGUE_WORDS,
    AFFIRMATIVE,
    NEGATIVE,
    LOW_CONFIDENCE_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD,
    NON_GOAL_PHRASES,
    GOAL_KEYWORDS,
    GOAL_FILLER_PHRASES
)

__all__ = [
    # Smart evaluation
    'evaluate_smart_goal_with_llm',
    'heuristic_smart_check',
    'create_concise_goal',
    
    # Session storage
    'save_session_data',
    'load_session_data',
    'load_session1_data_for_session2',
    
    # State prompts
    'get_session1_prompt',
    'get_session2_prompt',
    
    # Program loader
    'load_program_info',
    
    # Name extraction
    'extract_name_from_text',
    
    # State helpers
    'create_state_result',
    'check_affirmative',
    'check_negative',
    'extract_number',
    'check_wants_more',
    'check_done',
    
    # Discovery helpers
    'get_next_discovery_question',
    'get_discovery_prompt',
    'is_discovery_complete',
    'get_remaining_questions',
    'DISCOVERY_QUESTIONS',
    'DISCOVERY_PROMPTS',
    
    # Goal detection
    'is_likely_goal',
    'contains_goal_keywords',
    'is_goal_question',
    'is_too_short_for_goal',
    
    # Constants
    'TIME_WORDS',
    'DAYS_OF_WEEK',
    'ACTION_VERBS',
    'ACTIVITY_NAMES',
    'VAGUE_WORDS',
    'AFFIRMATIVE',
    'NEGATIVE',
    'LOW_CONFIDENCE_THRESHOLD',
    'HIGH_CONFIDENCE_THRESHOLD',
    'NON_GOAL_PHRASES',
    'GOAL_KEYWORDS',
    'GOAL_FILLER_PHRASES',
]