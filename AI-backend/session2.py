from enum import Enum
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
import re


class Session2State(Enum):
    """States for Session 2 conversation flow"""
    GREETINGS = "greetings"
    CHECK_IN_GOALS = "check_in_goals"
    STRESS_LEVEL = "stress_level"
    GOAL_COMPLETION = "goal_completion"
    GOALS_FOR_NEXT_WEEK = "goals_for_next_week"
    
    # Path 1: Same goals as last week
    SAME_GOALS_SUCCESSES_CHALLENGES = "same_goals_successes_challenges"
    SAME_NOT_SUCCESSFUL = "same_not_successful"
    SAME_SUCCESSFUL = "same_successful"
    SAME_MAKE_ATTAINABLE = "same_make_attainable"
    SAME_CHANGES_NEEDED = "same_changes_needed"
    SAME_SOLUTIONS = "same_solutions"
    
    # Path 2: Different goals (keeping some + making new)
    DIFFERENT_KEEPING_AND_NEW = "different_keeping_and_new"
    DIFFERENT_SUCCESSES_CHALLENGES = "different_successes_challenges"
    DIFFERENT_NOT_SUCCESSFUL = "different_not_successful"
    DIFFERENT_SUCCESSFUL = "different_successful"
    DIFFERENT_MAKE_ATTAINABLE = "different_make_attainable"
    DIFFERENT_CHANGES_NEEDED = "different_changes_needed"
    DIFFERENT_SOLUTIONS = "different_solutions"
    DIFFERENT_WORK_ON_NEW = "different_work_on_new"
    
    # Path 3: Just creating different goals
    JUST_NEW_GOALS = "just_new_goals"
    CHECK_SMART = "check_smart"
    REFINE_GOAL = "refine_goal"
    CONFIDENCE_CHECK = "confidence_check"
    LOW_CONFIDENCE = "low_confidence"
    HIGH_CONFIDENCE = "high_confidence"
    MAKE_ACHIEVABLE = "make_achievable"
    
    # Common end states
    REMEMBER_GOAL = "remember_goal"
    ANYTHING_ELSE = "anything_else"
    ADDRESS_CONCERNS = "address_concerns"
    END_SESSION = "end_session"


class Session2Manager:
    """Manages conversation flow for Session 2"""
    
    def __init__(self, session1_data: Dict = None, llm_client=None):
        self.state = Session2State.GREETINGS
        self.session_data = {
            "user_name": session1_data.get("user_name") if session1_data else None,
            "previous_goals": session1_data.get("goal_details", []) if session1_data else [],
            "stress_level": None,
            "goal_completion_status": {},
            "successes": [],
            "challenges": [],
            "path_chosen": None,  # "same", "different", "new"
            "goals_to_keep": [],
            "new_goals": [],
            "current_goal": None,
            "goal_smart_analysis": None,
            "smart_refinement_attempts": 0,
            "confidence_level": None,
            "changes_needed": {},
            "solutions": {},
            "session_start": datetime.now().isoformat(),
            "turn_count": 0,
            "last_coach_response": None,
            "tracking_method_discussed": False,
            "anything_else_asked": False
        }
        self.llm_client = llm_client
        
    def set_llm_client(self, llm_client):
        """Set the LLM client for SMART goal evaluation"""
        self.llm_client = llm_client
    
    def evaluate_smart_goal(self, goal: str) -> Dict[str, Any]:
        """Use LLM to evaluate if a goal is SMART"""
        if not self.llm_client:
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
            response = self.llm_client.evaluate_goal(evaluation_prompt)
            
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            analysis = json.loads(response)
            
            is_smart = all(
                analysis[criterion]["met"] 
                for criterion in ["specific", "measurable", "achievable", "relevant", "timebound"]
            )
            
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
            return self._heuristic_smart_check(goal)
    
    def _heuristic_smart_check(self, goal: str) -> Dict[str, Any]:
        """Simple heuristic-based SMART check as fallback"""
        goal_lower = goal.lower()
        
        has_numbers = bool(re.search(r'\d+', goal))
        time_words = ['day', 'week', 'month', 'year', 'daily', 'weekly', 'by', 'until', 'for']
        has_timeframe = any(word in goal_lower for word in time_words)
        action_verbs = ['exercise', 'walk', 'run', 'eat', 'drink', 'sleep', 'reduce', 'increase']
        has_action = any(verb in goal_lower for verb in action_verbs)
        
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
    
    def get_state(self) -> Session2State:
        return self.state
    
    def set_state(self, new_state: Session2State):
        self.state = new_state
    
    def get_system_prompt_addition(self) -> str:
        """Get state-specific system prompt additions"""
        
        previous_goals_summary = ""
        if self.session_data.get("previous_goals"):
            previous_goals_summary = "\n\nPrevious goals from Session 1:"
            for i, goal_info in enumerate(self.session_data["previous_goals"], 1):
                previous_goals_summary += f"\n  {i}. {goal_info['goal']} (Confidence: {goal_info.get('confidence', 'N/A')}/10)"
        
        prompts = {
            Session2State.GREETINGS: f"""
You are beginning Session 2. Welcome the participant back warmly!

IMPORTANT:
- Use their name: {self.session_data.get('user_name', 'there')}
- Be enthusiastic about seeing them again
- NO markdown or emojis
- Keep it brief and warm

Example: "Hi [name]! Great to see you again. How has your week been?"
{previous_goals_summary}""",
            
            Session2State.CHECK_IN_GOALS: f"""
Check in about their goals from last week.

Previous goals:
{previous_goals_summary}

Ask how things went with their goals. Be conversational and curious.
NO markdown or emojis.""",
            
            Session2State.STRESS_LEVEL: """
Ask about their stress level on a scale of 1-10.
- 1 = No stress at all
- 10 = Extremely stressed

Frame it naturally: "On a scale of 1 to 10, how would you rate your stress level this past week?"

NO markdown or emojis.""",
            
            Session2State.GOAL_COMPLETION: """
Ask about their goal completion. Did they complete their goals?
Be encouraging regardless of the answer.

NO markdown or emojis.""",
            
            Session2State.GOALS_FOR_NEXT_WEEK: """
Transition to next week's goals. Ask what they'd like to focus on:
- Same goals as last week?
- Different goals (keep some, add new)?
- Completely new goals?

NO markdown or emojis.""",
            
            Session2State.SAME_GOALS_SUCCESSES_CHALLENGES: """
They're keeping the same goals. Ask about successes and challenges.
"What went well? What was challenging?"

NO markdown or emojis.""",
            
            Session2State.SAME_NOT_SUCCESSFUL: """
They had challenges. Empathize and explore.
"Tell me more about what made it difficult."

NO markdown or emojis.""",
            
            Session2State.SAME_SUCCESSFUL: """
They had successes! Celebrate and dig deeper.
"That's wonderful! What helped you succeed?"

NO markdown or emojis.""",
            
            Session2State.SAME_MAKE_ATTAINABLE: """
Help them make the goal more attainable.
"How can we adjust this goal to make it feel more doable?"

NO markdown or emojis.""",
            
            Session2State.SAME_CHANGES_NEEDED: """
Ask if anything needs to change for next week.
"Is there anything you'd like to adjust about your approach?"

NO markdown or emojis.""",
            
            Session2State.SAME_SOLUTIONS: """
Work on solutions to challenges.
"What could help you overcome that challenge?"

NO markdown or emojis.""",
            
            Session2State.DIFFERENT_KEEPING_AND_NEW: """
They want to keep some goals and add new ones.
Ask which goals they want to keep and what new goals they'd like to add.

NO markdown or emojis.""",
            
            Session2State.DIFFERENT_SUCCESSES_CHALLENGES: """
Ask about successes and challenges with their previous goals.
"What went well? What was tough?"

NO markdown or emojis.""",
            
            Session2State.DIFFERENT_NOT_SUCCESSFUL: """
They struggled. Empathize and explore what happened.
"That's okay - tell me more about the challenges you faced."

NO markdown or emojis.""",
            
            Session2State.DIFFERENT_SUCCESSFUL: """
Celebrate their successes!
"That's fantastic! What helped make it work?"

NO markdown or emojis.""",
            
            Session2State.DIFFERENT_MAKE_ATTAINABLE: """
Help adjust goals to be more attainable.
"How can we make this feel more achievable for you?"

NO markdown or emojis.""",
            
            Session2State.DIFFERENT_CHANGES_NEEDED: """
Ask what needs to change for the goals they're keeping.
"What adjustments would help?"

NO markdown or emojis.""",
            
            Session2State.DIFFERENT_SOLUTIONS: """
Work on solutions together.
"What strategies could help you with that?"

NO markdown or emojis.""",
            
            Session2State.DIFFERENT_WORK_ON_NEW: """
Transition to their new goals.
"Great! Now let's talk about the new goal you'd like to add."

NO markdown or emojis.""",
            
            Session2State.JUST_NEW_GOALS: """
They want completely new goals.
Ask what they'd like to focus on this week.

NO markdown or emojis.""",
            
            Session2State.CHECK_SMART: """
The system evaluated the goal against SMART criteria.

If NOT SMART:
- Provide specific feedback on what's missing
- Guide them to refine it

If SMART:
- Celebrate!
- Move to confidence check

NO markdown or emojis.""",
            
            Session2State.REFINE_GOAL: """
Work to make the goal SMART:
- More Specific
- Measurable with metrics
- Achievable and realistic
- Relevant to their life
- Time-bound with a deadline

NO markdown or emojis.""",
            
            Session2State.CONFIDENCE_CHECK: """
Ask them to rate confidence (1-10 scale).
"On a scale of 1 to 10, how confident do you feel about achieving this goal?"

NO markdown or emojis.""",
            
            Session2State.LOW_CONFIDENCE: """
They have low confidence (≤7).
Explore what would make it more achievable.

NO markdown or emojis.""",
            
            Session2State.HIGH_CONFIDENCE: """
Great confidence (>7)! Celebrate it.

NO markdown or emojis.""",
            
            Session2State.MAKE_ACHIEVABLE: """
Help them adjust the goal to feel more achievable.
"What would make this goal feel more doable?"

NO markdown or emojis.""",
            
            Session2State.REMEMBER_GOAL: """
Ask how they'll remember/track their goal.
Suggest: phone reminders, writing it down, telling someone, scheduling.

NO markdown or emojis.""",
            
            Session2State.ANYTHING_ELSE: """
Ask if there's anything else they'd like to discuss.
"Is there anything else you'd like to talk about before we wrap up?"

NO markdown or emojis.""",
            
            Session2State.ADDRESS_CONCERNS: """
Address any final concerns or questions.
Be supportive and helpful.

NO markdown or emojis.""",
            
            Session2State.END_SESSION: """
Wrap up Session 2 warmly. Summarize their goals for next week.

IMPORTANT:
- Next session is in 1 week
- DO NOT promise to check in before then
- NO markdown or emojis

Example: "I'm excited to hear how next week goes. Remember to track your progress. See you at Session 3!"
"""
        }
        
        return prompts.get(self.state, "")
    
    def process_user_input(self, user_input: str, last_coach_response: str = None, 
                          conversation_history: list = None) -> Dict[str, Any]:
        """Process user input and determine state transitions"""
        user_lower = user_input.lower().strip()
        self.session_data["turn_count"] += 1
        
        if last_coach_response:
            self.session_data["last_coach_response"] = last_coach_response
        
        result = {
            "next_state": None,
            "context": "",
            "trigger_rag": True
        }
        
        # State machine logic
        if self.state == Session2State.GREETINGS:
            if user_input.strip() == "[START_SESSION]":
                result["context"] = "Welcome them back to Session 2. Use their name if available."
                return result
            
            result["next_state"] = Session2State.CHECK_IN_GOALS
            result["context"] = "Acknowledge their response. Transition to checking in about goals."
        
        elif self.state == Session2State.CHECK_IN_GOALS:
            result["next_state"] = Session2State.STRESS_LEVEL
            result["context"] = "Acknowledge how things went. Ask about stress level (1-10)."
        
        elif self.state == Session2State.STRESS_LEVEL:
            try:
                numbers = re.findall(r'\d+', user_input)
                if numbers:
                    stress = int(numbers[0])
                    self.session_data["stress_level"] = stress
                    result["next_state"] = Session2State.GOAL_COMPLETION
                    result["context"] = f"Stress level: {stress}/10. Acknowledge it. Ask about goal completion."
                else:
                    result["context"] = "Ask for numeric stress level (1-10)"
            except:
                result["context"] = "Ask for numeric stress level (1-10)"
        
        elif self.state == Session2State.GOAL_COMPLETION:
            completed = any(word in user_lower for word in ["yes", "yeah", "did", "completed", "finished", "accomplished"])
            not_completed = any(word in user_lower for word in ["no", "didn't", "didnt", "not", "partially", "some"])
            
            if completed or not_completed:
                result["next_state"] = Session2State.GOALS_FOR_NEXT_WEEK
                result["context"] = "Acknowledge completion status. Ask what they want to focus on next week."
            else:
                result["context"] = "Ask if they completed their goals."
        
        elif self.state == Session2State.GOALS_FOR_NEXT_WEEK:
            same_goals = any(phrase in user_lower for phrase in ["same", "continue", "keep going", "stick with"])
            different = any(phrase in user_lower for phrase in ["different", "some and", "keep some", "change", "adjust"])
            new_goals = any(phrase in user_lower for phrase in ["new", "completely different", "start fresh"])
            
            if same_goals and not different:
                self.session_data["path_chosen"] = "same"
                result["next_state"] = Session2State.SAME_GOALS_SUCCESSES_CHALLENGES
                result["context"] = "They're keeping same goals. Ask about successes and challenges."
            elif different:
                self.session_data["path_chosen"] = "different"
                result["next_state"] = Session2State.DIFFERENT_KEEPING_AND_NEW
                result["context"] = "They want to keep some and add new. Ask which to keep."
            elif new_goals:
                self.session_data["path_chosen"] = "new"
                result["next_state"] = Session2State.JUST_NEW_GOALS
                result["context"] = "They want new goals. Ask what they'd like to focus on."
            else:
                result["context"] = "Ask to clarify: same goals, different goals, or new goals?"
        
        # SAME GOALS PATH
        elif self.state == Session2State.SAME_GOALS_SUCCESSES_CHALLENGES:
            has_challenges = any(word in user_lower for word in ["challenge", "difficult", "hard", "struggle", "tough", "didn't", "couldn't"])
            has_success = any(word in user_lower for word in ["went well", "good", "great", "success", "accomplished", "did it"])
            
            if has_challenges and not has_success:
                result["next_state"] = Session2State.SAME_NOT_SUCCESSFUL
                result["context"] = "They had challenges. Explore what made it difficult."
            elif has_success:
                result["next_state"] = Session2State.SAME_SUCCESSFUL
                result["context"] = "They had success! Celebrate and ask what helped."
            else:
                result["context"] = "Ask about what went well and what was challenging."
        
        elif self.state == Session2State.SAME_NOT_SUCCESSFUL:
            result["next_state"] = Session2State.SAME_MAKE_ATTAINABLE
            result["context"] = "Acknowledge challenges. Ask how to make it more attainable."
        
        elif self.state == Session2State.SAME_SUCCESSFUL:
            result["next_state"] = Session2State.SAME_CHANGES_NEEDED
            result["context"] = "Great! Ask if anything needs to change for next week."
        
        elif self.state == Session2State.SAME_MAKE_ATTAINABLE:
            result["next_state"] = Session2State.SAME_CHANGES_NEEDED
            result["context"] = "Acknowledge adjustment ideas. Ask about any other changes needed."
        
        elif self.state == Session2State.SAME_CHANGES_NEEDED:
            needs_changes = any(word in user_lower for word in ["yes", "yeah", "change", "adjust", "different"])
            no_changes = any(word in user_lower for word in ["no", "nope", "keep", "same", "good"])
            
            if needs_changes:
                result["next_state"] = Session2State.SAME_SOLUTIONS
                result["context"] = "Ask what specific changes would help."
            elif no_changes:
                result["next_state"] = Session2State.REMEMBER_GOAL
                result["context"] = "Good! Ask how they'll remember their goal."
            else:
                result["context"] = "Ask if anything needs to change for next week."
        
        elif self.state == Session2State.SAME_SOLUTIONS:
            result["next_state"] = Session2State.REMEMBER_GOAL
            result["context"] = "Acknowledge solutions. Ask about tracking method."
        
        # DIFFERENT GOALS PATH
        elif self.state == Session2State.DIFFERENT_KEEPING_AND_NEW:
            result["next_state"] = Session2State.DIFFERENT_SUCCESSES_CHALLENGES
            result["context"] = "Note which goals they're keeping. Ask about successes/challenges."
        
        elif self.state == Session2State.DIFFERENT_SUCCESSES_CHALLENGES:
            has_challenges = any(word in user_lower for word in ["challenge", "difficult", "hard", "struggle"])
            has_success = any(word in user_lower for word in ["went well", "good", "success"])
            
            if has_challenges and not has_success:
                result["next_state"] = Session2State.DIFFERENT_NOT_SUCCESSFUL
                result["context"] = "Explore challenges."
            elif has_success:
                result["next_state"] = Session2State.DIFFERENT_SUCCESSFUL
                result["context"] = "Celebrate success!"
            else:
                result["context"] = "Ask about successes and challenges."
        
        elif self.state == Session2State.DIFFERENT_NOT_SUCCESSFUL:
            result["next_state"] = Session2State.DIFFERENT_MAKE_ATTAINABLE
            result["context"] = "Ask how to make it more attainable."
        
        elif self.state == Session2State.DIFFERENT_SUCCESSFUL:
            result["next_state"] = Session2State.DIFFERENT_CHANGES_NEEDED
            result["context"] = "Ask about changes needed."
        
        elif self.state == Session2State.DIFFERENT_MAKE_ATTAINABLE:
            result["next_state"] = Session2State.DIFFERENT_CHANGES_NEEDED
            result["context"] = "Acknowledge adjustments. Ask about other changes."
        
        elif self.state == Session2State.DIFFERENT_CHANGES_NEEDED:
            needs_changes = any(word in user_lower for word in ["yes", "change", "adjust"])
            no_changes = any(word in user_lower for word in ["no", "keep", "same"])
            
            if needs_changes:
                result["next_state"] = Session2State.DIFFERENT_SOLUTIONS
                result["context"] = "Ask for specific solutions."
            elif no_changes:
                result["next_state"] = Session2State.DIFFERENT_WORK_ON_NEW
                result["context"] = "Good! Now let's work on new goals."
            else:
                result["context"] = "Ask if changes are needed."
        
        elif self.state == Session2State.DIFFERENT_SOLUTIONS:
            result["next_state"] = Session2State.DIFFERENT_WORK_ON_NEW
            result["context"] = "Acknowledge solutions. Transition to new goals."
        
        elif self.state == Session2State.DIFFERENT_WORK_ON_NEW:
            goal_candidate = user_input.strip()
            
            if len(goal_candidate.split()) > 3:
                self.session_data["current_goal"] = goal_candidate
                self.session_data["new_goals"].append(goal_candidate)
                
                smart_eval = self.evaluate_smart_goal(goal_candidate)
                self.session_data["goal_smart_analysis"] = smart_eval
                
                if smart_eval["is_smart"]:
                    result["next_state"] = Session2State.CONFIDENCE_CHECK
                    result["context"] = f"Goal is SMART! Ask for confidence."
                else:
                    result["next_state"] = Session2State.CHECK_SMART
                    result["context"] = f"Goal needs work. Missing: {', '.join(smart_eval['missing_criteria'])}"
            else:
                result["context"] = "Ask what new goal they'd like to set."
        
        # NEW GOALS PATH
        elif self.state == Session2State.JUST_NEW_GOALS:
            goal_candidate = user_input.strip()
            
            if len(goal_candidate.split()) > 3:
                self.session_data["current_goal"] = goal_candidate
                self.session_data["new_goals"].append(goal_candidate)
                
                smart_eval = self.evaluate_smart_goal(goal_candidate)
                self.session_data["goal_smart_analysis"] = smart_eval
                
                if smart_eval["is_smart"]:
                    result["next_state"] = Session2State.CONFIDENCE_CHECK
                    result["context"] = "Goal is SMART! Ask confidence."
                else:
                    result["next_state"] = Session2State.CHECK_SMART
                    result["context"] = f"Needs refinement. Missing: {', '.join(smart_eval['missing_criteria'])}"
            else:
                result["context"] = "Ask what goal they'd like to focus on."
        
        elif self.state == Session2State.CHECK_SMART:
            smart_analysis = self.session_data.get("goal_smart_analysis", {})
            is_smart = smart_analysis.get("is_smart", False)
            
            if is_smart:
                result["next_state"] = Session2State.CONFIDENCE_CHECK
                result["context"] = "Goal is SMART! Ask confidence."
            else:
                result["next_state"] = Session2State.REFINE_GOAL
                result["context"] = "Guide refinement."
        
        elif self.state == Session2State.REFINE_GOAL:
            goal_candidate = user_input.strip()
            
            if len(goal_candidate.split()) > 3:
                self.session_data["current_goal"] = goal_candidate
                if self.session_data["new_goals"]:
                    self.session_data["new_goals"][-1] = goal_candidate
                
                smart_eval = self.evaluate_smart_goal(goal_candidate)
                self.session_data["goal_smart_analysis"] = smart_eval
                
                if smart_eval["is_smart"]:
                    result["next_state"] = Session2State.CONFIDENCE_CHECK
                    result["context"] = "Refined goal is SMART! Ask confidence."
                else:
                    self.session_data["smart_refinement_attempts"] += 1
                    if self.session_data["smart_refinement_attempts"] >= 3:
                        result["next_state"] = Session2State.CONFIDENCE_CHECK
                        result["context"] = "Move forward with current goal. Ask confidence."
                    else:
                        result["context"] = "Continue refinement."
            else:
                result["context"] = "Ask them to refine the goal."
        
        elif self.state == Session2State.CONFIDENCE_CHECK:
            try:
                numbers = re.findall(r'\d+', user_input)
                if numbers:
                    confidence = int(numbers[0])
                    self.session_data["confidence_level"] = confidence
                    
                    if confidence <= 7:
                        result["next_state"] = Session2State.LOW_CONFIDENCE
                    else:
                        result["next_state"] = Session2State.HIGH_CONFIDENCE
                else:
                    result["context"] = "Ask for numeric confidence (1-10)"
            except:
                result["context"] = "Ask for numeric confidence (1-10)"
        
        elif self.state == Session2State.LOW_CONFIDENCE:
            result["next_state"] = Session2State.MAKE_ACHIEVABLE
            result["context"] = "Explore what would make it more achievable."
        
        elif self.state == Session2State.HIGH_CONFIDENCE:
            result["next_state"] = Session2State.REMEMBER_GOAL
            result["context"] = "Great confidence! Ask about tracking."
        
        elif self.state == Session2State.MAKE_ACHIEVABLE:
            result["next_state"] = Session2State.REMEMBER_GOAL
            result["context"] = "Acknowledge adjustments. Ask about tracking."
        
        elif self.state == Session2State.REMEMBER_GOAL:
            tracking_methods = ['calendar', 'reminder', 'app', 'note', 'journal', 'planner']
            described_tracking = any(method in user_lower for method in tracking_methods)
            
            if described_tracking:
                self.session_data["tracking_method_discussed"] = True
            
            if not self.session_data.get("anything_else_asked"):
                result["next_state"] = Session2State.ANYTHING_ELSE
                result["context"] = "Acknowledge tracking. Ask if anything else to discuss."
            else:
                result["next_state"] = Session2State.END_SESSION
                result["context"] = "Wrap up session."
        
        elif self.state == Session2State.ANYTHING_ELSE:
            self.session_data["anything_else_asked"] = True
            
            has_concerns = any(word in user_lower for word in ["yes", "yeah", "question", "concern", "worried"])
            no_concerns = any(word in user_lower for word in ["no", "nope", "nothing", "all good", "im good"])
            
            if has_concerns:
                result["next_state"] = Session2State.ADDRESS_CONCERNS
                result["context"] = "Address their concern."
            elif no_concerns:
                result["next_state"] = Session2State.END_SESSION
                result["context"] = "Wrap up warmly."
            else:
                result["context"] = "Ask if there's anything else."
        
        elif self.state == Session2State.ADDRESS_CONCERNS:
            result["next_state"] = Session2State.END_SESSION
            result["context"] = "Concern addressed. Wrap up session."
        
        elif self.state == Session2State.END_SESSION:
            result["context"] = "Session complete."
        
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
            filename = f"session2_{timestamp}.json"
        
        data = {
            "state": self.state.value,
            "session_data": self.session_data,
            "conversation_history": conversation_history or []
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def load_session(self, filename: str):
        """Load session data from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.state = Session2State(data["state"])
        self.session_data = data["session_data"]
        
        return data.get("conversation_history", [])