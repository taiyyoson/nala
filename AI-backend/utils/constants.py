"""
Shared constants used across session managers.
"""

# Time-related words for SMART checking
TIME_WORDS = [
    'day', 'week', 'month', 'year', 'daily', 'weekly', 'monthly',
    'per week', 'per day', 'times', 'every', 'each', 'by', 'for',
    'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'monday'
]

# Day names
DAYS_OF_WEEK = [
    'monday', 'tuesday', 'wednesday', 'thursday', 
    'friday', 'saturday', 'sunday'
]

# Action verbs for SMART goals
ACTION_VERBS = [
    'walk', 'run', 'exercise', 'eat', 'drink', 'sleep', 'reduce',
    'increase', 'practice', 'meditate', 'stretch', 'play'
]

# Activity names
ACTIVITY_NAMES = [
    'pokemon go', 'yoga', 'gym', 'swimming', 'biking', 'hiking'
]

# Vague words (anti-pattern for SMART goals)
VAGUE_WORDS = [
    'more', 'better', 'less', 'healthier', 'improve'
]

# Affirmative responses
AFFIRMATIVE = [
    "yes", "yeah", "yep", "sure", "yup", "ok", "okay", "i do", "i have"
]

# Negative responses
NEGATIVE = [
    "no", "nope", "nah", "not really", "don't", "dont", "no questions"
]

# Confidence thresholds
LOW_CONFIDENCE_THRESHOLD = 7
HIGH_CONFIDENCE_THRESHOLD = 8

# Non-goal phrases (indicate user is NOT stating a goal)
NON_GOAL_PHRASES = [
    'no', 'yes', 'maybe', 'i dont know', "i don't know", 'not sure',
    'just want to stick', 'thats all', "that's all", 'nothing else',
    'im good', "i'm good", 'no more', 'nope', 'nah'
]

# Goal-related keywords
GOAL_KEYWORDS = [
    "want to", "goal is", "goal:", "would like to", "hoping to", 
    "trying to", "plan to", "i want", "my goal"
]

# Filler phrases to remove when creating concise goals
GOAL_FILLER_PHRASES = [
    "i want to", "i would like to", "i'm going to", "i will",
    "my goal is to", "the goal is to", "i plan to"
]