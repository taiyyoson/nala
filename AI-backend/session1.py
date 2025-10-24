from enum import Enum
from typing import Dict, Any, Optional, Tuple
import json
import os
from datetime import datetime
import re


class SessionState(Enum):
    """States for Session 1 conversation flow"""
    GREETINGS = "greetings"
    PROGRAM_DETAILS = "program_details"
    QUESTIONS_ABOUT_PROGRAM = "questions_about_program"
    AWAITING_YES_NO = "awaiting_yes_no"
    ANSWERING_QUESTION = "answering_question"
    PROMPT_TALK_ABOUT_SELF = "prompt_talk_about_self"
    GOALS = "goals"
    CHECK_SMART = "check_smart"
    REFINE_GOAL = "refine_goal"
    CONFIDENCE_CHECK = "confidence_check"
    LOW_CONFIDENCE = "low_confidence"
    HIGH_CONFIDENCE = "high_confidence"
    ASK_MORE_GOALS = "ask_more_goals"  # NEW: Ask if they want to add more goals
    REMEMBER_GOAL = "remember_goal"
    END_SESSION = "end_session"


class Session1Manager:
    """Manages conversation flow for Session 1"""
    
    def __init__(self, program_info_file: str = "program_info.txt", llm_client=None):
        self.state = SessionState.GREETINGS
        self.session_data = {
            "user_name": None,
            "program_questions_asked": [],
            "goals": [],
            "current_goal": None,
            "goal_smart_analysis": None,
            "smart_refinement_attempts": 0,
            "confidence_level": None,
            "session_start": datetime.now().isoformat(),
            "turn_count": 0
        }
        self.program_info_file = program_info_file
        self.program_info = self._load_program_info()
        self.llm_client = llm_client  # For SMART evaluation
        
    def _load_program_info(self) -> str:
        """Load program information from text file"""
        try:
            if os.path.exists(self.program_info_file):
                with open(self.program_info_file, 'r') as f:
                    return f.read()
            else:
                return """Default Program Information:
This is a 12-week health and wellness coaching program designed to help you achieve your personal health goals.
- Weekly 1-on-1 coaching sessions
- Personalized goal setting and tracking
- Evidence-based behavior change strategies
- Nutrition and exercise guidance
- Accountability and support throughout your journey"""
        except Exception as e:
            print(f"Error loading program info: {e}")
            return "Program information unavailable."
    
    def set_llm_client(self, llm_client):
        """Set the LLM client for SMART goal evaluation"""
        self.llm_client = llm_client
    
    def set_llm_client(self, llm_client):
        """Set the LLM client for SMART goal evaluation"""
        self.llm_client = llm_client
    
    def evaluate_smart_goal(self, goal: str) -> Dict[str, Any]:
        """
        Use LLM to evaluate if a goal is SMART
        
        Returns:
            {
                'is_smart': bool,
                'analysis': {
                    'specific': {'met': bool, 'issue': str},
                    'measurable': {'met': bool, 'issue': str},
                    'achievable': {'met': bool, 'issue': str},
                    'relevant': {'met': bool, 'issue': str},
                    'timebound': {'met': bool, 'issue': str}
                },
                'suggestions': str,
                'missing_criteria': list
            }
        """
        if not self.llm_client:
            # Fallback to simple heuristic if no LLM client
            return self._heuristic_smart_check(goal)
        
        evaluation_prompt = f"""Evaluate if this goal is SMART (Specific, Measurable, Achievable, Relevant, Time-bound).

Goal: "{goal}"

Analyze each SMART criterion and respond ONLY with a JSON object in this exact format:
{{
    "specific": {{"met": true, "issue": ""}},
    "measurable": {{"met": false, "issue": "No specific numbers or metrics"}},
    "achievable": {{"met": true, "issue": ""}},
    "relevant": {{"met": true, "issue": ""}},
    "timebound": {{"met": false, "issue": "No deadline or timeframe specified"}},
    "suggestions": "Add specific amount (e.g., 10 pounds) and timeframe (e.g., in 3 months)"
}}

Be strict but fair. A goal should have:
- Specific: Clear, detailed action (not vague like "be healthier")
- Measurable: Quantifiable metric (numbers, frequency, duration)
- Achievable: Realistic given typical constraints
- Relevant: Related to health/wellness
- Time-bound: Has a deadline or timeframe

IMPORTANT: Respond with ONLY the JSON object, no other text before or after."""

        try:
            # Call LLM for evaluation
            response = self.llm_client.evaluate_goal(evaluation_prompt)
            
            # Clean up response - remove any markdown code blocks
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse JSON response
            analysis = json.loads(response)
            
            # Determine if goal is SMART (all criteria met)
            is_smart = all(
                analysis[criterion]["met"] 
                for criterion in ["specific", "measurable", "achievable", "relevant", "timebound"]
            )
            
            # Get missing criteria
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
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"LLM Response was: {response[:200]}...")
            # Fallback to heuristic
            return self._heuristic_smart_check(goal)
        except Exception as e:
            print(f"Error in SMART evaluation: {e}")
            return self._heuristic_smart_check(goal)
    
    def _heuristic_smart_check(self, goal: str) -> Dict[str, Any]:
        """Simple heuristic-based SMART check as fallback"""
        goal_lower = goal.lower()
        
        # Check for numbers (measurable/timebound indicators)
        has_numbers = bool(re.search(r'\d+', goal))
        
        # Check for time words
        time_words = ['day', 'week', 'month', 'year', 'daily', 'weekly', 'by', 'until', 'for']
        has_timeframe = any(word in goal_lower for word in time_words)
        
        # Check for action verbs (specific)
        action_verbs = ['exercise', 'walk', 'run', 'eat', 'drink', 'sleep', 'reduce', 'increase']
        has_action = any(verb in goal_lower for verb in action_verbs)
        
        # Simple scoring
        is_smart = has_numbers and has_timeframe and has_action and len(goal.split()) > 5
        
        missing = []
        if not has_action: missing.append("SPECIFIC")
        if not has_numbers: missing.append("MEASURABLE")
        if not has_timeframe: missing.append("TIME-BOUND")
        
        return {
            'is_smart': is_smart,
            'analysis': {
                'specific': {'met': has_action, 'issue': 'Goal needs a clear action verb'},
                'measurable': {'met': has_numbers, 'issue': 'Goal needs specific numbers/metrics'},
                'achievable': {'met': True, 'issue': ''},
                'relevant': {'met': True, 'issue': ''},
                'timebound': {'met': has_timeframe, 'issue': 'Goal needs a timeframe or deadline'}
            },
            'suggestions': 'Add specific numbers and a timeframe to make this goal SMART.',
            'missing_criteria': missing
        }
    
    def get_state(self) -> SessionState:
        """Get current conversation state"""
        return self.state
    
    def set_state(self, new_state: SessionState):
        """Manually set conversation state"""
        self.state = new_state
    
    def get_system_prompt_addition(self) -> str:
        """Get state-specific system prompt additions"""
        prompts = {
            SessionState.GREETINGS: """
You are beginning Session 1. Warmly greet the participant and introduce yourself as Nala, their AI health coach.
Ask for their name and express enthusiasm about working with them on their health journey.""",
            
            SessionState.PROGRAM_DETAILS: f"""
Explain the program details to the participant. Here is the program information:

{self.program_info}

Keep it conversational and engaging. After explaining, transition naturally to asking if they have questions.""",
            
            SessionState.QUESTIONS_ABOUT_PROGRAM: """
The participant may have questions about the program. Be ready to answer them based on the program information provided.
After answering, ask if they have any more questions.""",
            
            SessionState.PROMPT_TALK_ABOUT_SELF: """
Transition from program questions to getting to know the participant better.
Prompt them to talk about themselves, their current situation, and what brought them to this program.
Be warm and inviting.""",
            
            SessionState.GOALS: """
Guide the participant to articulate their goals. Ask open-ended questions like:
- What would you like to achieve through this program?
- What changes are you hoping to make?
Help them express their goals clearly.""",
            
            SessionState.CHECK_SMART: """
The system has evaluated the participant's goal against SMART criteria.
DO NOT ask the participant if they think it's SMART - the system has already analyzed it.
Instead, provide feedback based on the analysis provided in the additional context.""",
            
            SessionState.REFINE_GOAL: """
The goal needs refinement to be SMART. Work collaboratively with the participant to make their goal:
- More Specific
- Measurable with clear metrics
- Achievable and realistic
- Relevant to their life
- Time-bound with a deadline""",
            
            SessionState.CONFIDENCE_CHECK: """
Ask the participant to rate their confidence in achieving this goal on a scale of 1-10.
Be supportive regardless of their answer.""",
            
            SessionState.LOW_CONFIDENCE: """
The participant has low confidence (≤7). This is okay!
Explore what would make the goal more achievable. Consider suggesting they rework it to be more attainable.
Ask: "What would make this goal feel more doable for you?" """,
            
            SessionState.HIGH_CONFIDENCE: """
Great! The participant has high confidence (>7).
Celebrate their confidence and move forward.""",
            
            SessionState.REMEMBER_GOAL: """
Help the participant create a plan for remembering and tracking their goal.
Ask: "How will you remember to work on your goal?" 
Suggest strategies like:
- Setting phone reminders
- Writing it down where they'll see it
- Telling a friend or family member
- Scheduling specific times for goal-related activities""",
            
            SessionState.END_SESSION: """
Wrap up the session warmly. Summarize what you discussed:
- Their goal(s)
- Their confidence level
- Their plan for remembering/tracking
Thank them and express enthusiasm for the next session."""
        }
        
        return prompts.get(self.state, "")
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and determine state transitions
        
        Returns:
            Dict with:
                - next_state: SessionState or None to keep current
                - context: Additional context for the LLM
                - trigger_rag: bool, whether to use RAG for this response
        """
        user_lower = user_input.lower().strip()
        self.session_data["turn_count"] += 1
        
        result = {
            "next_state": None,
            "context": "",
            "trigger_rag": True  # Default: use RAG
        }
        
        # State machine logic
        if self.state == SessionState.GREETINGS:
            # Extract name if present
            if any(word in user_lower for word in ["i'm", "im", "my name is", "call me"]):
                # Simple name extraction (can be improved)
                words = user_input.split()
                for i, word in enumerate(words):
                    if word.lower() in ["i'm", "im", "name", "call"]:
                        if i + 1 < len(words):
                            self.session_data["user_name"] = words[i + 1].strip('.,!?')
                            break
            
            result["next_state"] = SessionState.PROGRAM_DETAILS
            result["context"] = f"User's name: {self.session_data.get('user_name', 'unknown')}"
        
        elif self.state == SessionState.PROGRAM_DETAILS:
            result["next_state"] = SessionState.QUESTIONS_ABOUT_PROGRAM
        
        elif self.state == SessionState.QUESTIONS_ABOUT_PROGRAM:
            result["next_state"] = SessionState.AWAITING_YES_NO
            result["trigger_rag"] = False  # Program info should come from file
            result["context"] = f"Program Info:\n{self.program_info}"
        
        elif self.state == SessionState.AWAITING_YES_NO:
            # Check for yes/no response
            if any(word in user_lower for word in ["yes", "yeah", "yep", "sure", "i do"]):
                result["next_state"] = SessionState.ANSWERING_QUESTION
                self.session_data["program_questions_asked"].append(user_input)
            elif any(word in user_lower for word in ["no", "nope", "nah", "don't", "dont"]):
                result["next_state"] = SessionState.PROMPT_TALK_ABOUT_SELF
            else:
                # Ambiguous, stay in this state
                result["context"] = "Ask user to clarify: do they have questions (yes/no)?"
        
        elif self.state == SessionState.ANSWERING_QUESTION:
            # After answering, loop back to ask if more questions
            result["next_state"] = SessionState.QUESTIONS_ABOUT_PROGRAM
            result["trigger_rag"] = False
            result["context"] = f"Program Info:\n{self.program_info}"
        
        elif self.state == SessionState.PROMPT_TALK_ABOUT_SELF:
            result["next_state"] = SessionState.GOALS
        
        elif self.state == SessionState.GOALS:
            # Store the goal and evaluate it
            self.session_data["current_goal"] = user_input
            self.session_data["goals"].append(user_input)
            self.session_data["smart_refinement_attempts"] = 0
            
            # Evaluate SMART criteria
            smart_eval = self.evaluate_smart_goal(user_input)
            self.session_data["goal_smart_analysis"] = smart_eval
            
            if smart_eval["is_smart"]:
                # Goal is SMART! Move to confidence check
                result["next_state"] = SessionState.CONFIDENCE_CHECK
                result["context"] = f"Goal is SMART! Celebrate and move to confidence check.\nGoal: {user_input}"
            else:
                # Goal needs work
                result["next_state"] = SessionState.CHECK_SMART
                missing = ", ".join(smart_eval["missing_criteria"])
                result["context"] = f"""SMART Analysis:
Goal: "{user_input}"
Is SMART: No
Missing: {missing}
Suggestions: {smart_eval['suggestions']}

Gently explain what's missing and guide them to refine the goal. Be encouraging!"""
        
        elif self.state == SessionState.CHECK_SMART:
            # User has received feedback, staying in this state to guide them
            # They should be refining their goal now
            result["next_state"] = SessionState.REFINE_GOAL
            result["context"] = "User is ready to refine their goal based on feedback."
        
        elif self.state == SessionState.REFINE_GOAL:
            # User has provided a refined goal - evaluate it again
            self.session_data["current_goal"] = user_input
            self.session_data["smart_refinement_attempts"] += 1
            
            # Re-evaluate SMART criteria
            smart_eval = self.evaluate_smart_goal(user_input)
            self.session_data["goal_smart_analysis"] = smart_eval
            
            if smart_eval["is_smart"]:
                # Success! Goal is now SMART
                result["next_state"] = SessionState.CONFIDENCE_CHECK
                result["context"] = f"Excellent! The refined goal is now SMART. Celebrate their effort!\nRefined Goal: {user_input}"
            else:
                # Still needs work - but be more encouraging
                missing = ", ".join(smart_eval["missing_criteria"])
                attempts = self.session_data["smart_refinement_attempts"]
                
                if attempts >= 3:
                    # After 3 attempts, be more helpful and collaborative
                    result["context"] = f"""SMART Analysis (Attempt {attempts}):
Goal: "{user_input}"
Still missing: {missing}

After {attempts} attempts, offer to work WITH them more directly. 
Suggest a specific SMART version they could use or adapt. Make it collaborative and supportive."""
                else:
                    result["context"] = f"""SMART Analysis (Attempt {attempts}):
Goal: "{user_input}"
Still missing: {missing}
Suggestions: {smart_eval['suggestions']}

Provide specific, actionable feedback. What exact changes would make this SMART?"""
                
                # Stay in REFINE_GOAL state to keep looping
                result["next_state"] = SessionState.REFINE_GOAL
        
        elif self.state == SessionState.CONFIDENCE_CHECK:
            # Extract confidence level
            try:
                # Look for numbers in input
                import re
                numbers = re.findall(r'\d+', user_input)
                if numbers:
                    confidence = int(numbers[0])
                    self.session_data["confidence_level"] = confidence
                    
                    if confidence <= 7:
                        result["next_state"] = SessionState.LOW_CONFIDENCE
                    else:
                        result["next_state"] = SessionState.HIGH_CONFIDENCE
                else:
                    result["context"] = "Ask for numeric confidence rating (1-10)"
            except:
                result["context"] = "Ask for numeric confidence rating (1-10)"
        
        elif self.state == SessionState.LOW_CONFIDENCE:
            # After discussing, may go back to goals or forward
            if "rework" in user_lower or "change" in user_lower or "different" in user_lower:
                result["next_state"] = SessionState.GOALS
            else:
                result["next_state"] = SessionState.REMEMBER_GOAL
        
        elif self.state == SessionState.HIGH_CONFIDENCE:
            result["next_state"] = SessionState.REMEMBER_GOAL
        
        elif self.state == SessionState.REMEMBER_GOAL:
            result["next_state"] = SessionState.END_SESSION
        
        elif self.state == SessionState.END_SESSION:
            result["context"] = "Session is complete. Thank the user."
        
        return result
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of session data"""
        return {
            "current_state": self.state.value,
            "session_data": self.session_data,
            "duration_turns": self.session_data["turn_count"]
        }
    
    def save_session(self, filename: str = None, conversation_history: list = None):
        """Save session data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session1_{timestamp}.json"
        
        data = {
            "state": self.state.value,
            "session_data": self.session_data,
            "conversation_history": conversation_history or []  # Save history too
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def load_session(self, filename: str):
        """Load session data from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.state = SessionState(data["state"])
        self.session_data = data["session_data"]
        
        # Return conversation history if it exists
        return data.get("conversation_history", [])