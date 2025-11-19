"""
Utility for loading program information.
"""
import os


def load_program_info(filename: str = "program_info.txt") -> str:
    """
    Load program information from text file.
    
    Args:
        filename: Path to program info file
        
    Returns:
        Program information text or default message
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return f.read()
        else:
            return """Default Program Information:
This is a 4-week health and wellness coaching program designed to help you achieve your personal health goals.
- Weekly 1-on-1 coaching sessions
- Personalized goal setting and tracking
- Evidence-based behavior change strategies
- Nutrition and exercise guidance
- Accountability and support throughout your journey"""
    except Exception as e:
        return "Program information unavailable."