"""
Post-response constraint checker to catch and flag impossible promises
Can be integrated into the session chatbot to validate responses
"""

import re


class ConstraintChecker:
    """Checks if coach responses violate program constraints"""
    
    # Phrases that indicate impossible promises
    FORBIDDEN_PROMISES = [
        # Check-in promises
        r"\b(check in|checking in|check-in)\b.*\b(with you|tomorrow|this week|soon|later)\b",
        r"\b(i'll|i will|let me)\s+(check in|reach out|follow up|contact you)\b",
        r"\b(send|email|text|call|message)\s+you\b",
        
        # Mid-week contact
        r"\b(touch base|connect)\s+(with you|tomorrow|this week|midweek|mid-week)\b",
        r"\b(hear from|talk to)\s+you\s+(before|tomorrow|this week|soon)\b",
        
        # Reminder promises
        r"\b(send|set)\s+(you\s+)?(a\s+)?reminders?\b",
        r"\b(remind you|i'll remind)\b",
        
        # Daily/frequent contact
        r"\b(daily|everyday|every day)\s+(check-?in|update|contact)\b",
        r"\b(between sessions?|before next session)\b.*\b(contact|reach out|check in)\b",
    ]
    
    # Acceptable alternatives
    ACCEPTABLE_PHRASES = [
        r"\bat\s+(our\s+)?next\s+session\b",
        r"\bnext\s+week\b",
        r"\bsee you\s+(next week|at session \d+)\b",
        r"\b(track|monitor|record)\s+(your|yourself)\b",
        r"\byou\s+can\s+(track|use|set)\b",
        r"\bremind yourself\b",
        r"\bset\s+(your own|personal)\s+reminders?\b",
    ]
    
    def __init__(self):
        self.forbidden_patterns = [re.compile(pattern, re.IGNORECASE) 
                                   for pattern in self.FORBIDDEN_PROMISES]
        self.acceptable_patterns = [re.compile(pattern, re.IGNORECASE) 
                                   for pattern in self.ACCEPTABLE_PHRASES]
    
    def check_response(self, response: str) -> dict:
        """
        Check if response violates constraints
        
        Returns:
            {
                'valid': bool,
                'violations': list of strings,
                'suggestions': list of strings
            }
        """
        violations = []
        suggestions = []
        
        # Check for forbidden promises
        for pattern in self.forbidden_patterns:
            matches = pattern.findall(response)
            if matches:
                violations.append(f"Found forbidden promise: '{matches[0]}'")
        
        # Check for acceptable alternatives (good practices)
        has_good_alternatives = any(pattern.search(response) 
                                   for pattern in self.acceptable_patterns)
        
        # Generate suggestions if violations found
        if violations:
            suggestions.append("Instead of promising to check in, suggest:")
            suggestions.append("  - 'We'll discuss your progress at next week's session'")
            suggestions.append("  - 'Track your progress this week using [method]'")
            suggestions.append("  - 'Set reminders on your phone to help you remember'")
            suggestions.append("  - 'I look forward to hearing how it goes next week'")
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'suggestions': suggestions,
            'has_good_alternatives': has_good_alternatives
        }
    
    def get_correction_prompt(self, original_response: str, violations: list) -> str:
        """Generate a prompt to correct the response"""
        return f"""The following response violates program constraints:

"{original_response}"

Violations:
{chr(10).join(f"- {v}" for v in violations)}

Remember:
- This is a 4-session program with sessions exactly 1 week apart
- NO contact between sessions (no check-ins, calls, emails, or messages)
- Participants track their own progress between sessions

Please rewrite the response to:
1. Remove any promises of check-ins or contact between sessions
2. Emphasize participant's responsibility for self-tracking
3. Refer to "next week's session" instead of "checking in"
4. Encourage self-accountability methods

Rewrite:"""


def validate_and_correct_response(response: str, chatbot=None) -> tuple:
    """
    Validate response and optionally auto-correct if violations found
    
    Returns:
        (corrected_response, had_violations, correction_log)
    """
    checker = ConstraintChecker()
    result = checker.check_response(response)
    
    if result['valid']:
        return response, False, None
    
    # Log violations
    log = {
        'original': response,
        'violations': result['violations'],
        'suggestions': result['suggestions']
    }
    
    # If chatbot provided, can auto-correct
    if chatbot:
        correction_prompt = checker.get_correction_prompt(
            response, 
            result['violations']
        )
        # Could call LLM here to rewrite
        # corrected = chatbot.generate_correction(correction_prompt)
        # For now, just flag it
        print(f"\n⚠️  CONSTRAINT VIOLATION DETECTED:")
        for v in result['violations']:
            print(f"   - {v}")
        print(f"\nSuggestions:")
        for s in result['suggestions']:
            print(f"   {s}")
    
    return response, True, log


# Example usage
if __name__ == "__main__":
    checker = ConstraintChecker()
    
    # Test cases
    test_responses = [
        # BAD - should flag
        "Great goal! I'll check in with you tomorrow to see how it's going.",
        "I'll send you a reminder email this week to track your progress.",
        "Let me follow up with you mid-week to see how you're doing.",
        "I'll reach out before next session to check your progress.",
        
        # GOOD - should pass
        "Great goal! Track your progress this week, and we'll discuss how it went at next week's session.",
        "Set reminders on your phone to help you remember. I look forward to hearing about your progress next week!",
        "You can use a journal to track your daily progress. We'll review everything at Session 2 next week.",
        "I'm excited to hear how your first week goes! See you next Tuesday at our Session 2.",
    ]
    
    print("=" * 70)
    print("CONSTRAINT CHECKER - TEST RESULTS")
    print("=" * 70)
    
    for i, response in enumerate(test_responses, 1):
        print(f"\nTest {i}: {response[:60]}...")
        result = checker.check_response(response)
        
        if result['valid']:
            print("   ✅ VALID - No constraint violations")
            if result['has_good_alternatives']:
                print("   👍 Contains good self-tracking language")
        else:
            print("   ❌ INVALID - Violations found:")
            for v in result['violations']:
                print(f"      - {v}")