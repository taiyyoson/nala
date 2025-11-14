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
    DISCOVERY_QUESTIONS = "discovery_questions"
    GOAL_COMPLETION = "goal_completion"
    GOALS_FOR_NEXT_WEEK = "goals_for_next_week"
    
    # Path 1: Same goals as last week
    SAME_GOALS_SUCCESSES_CHALLENGES = "same_goals_successes_challenges"
    SAME_ANYTHING_TO_CHANGE = "same_anything_to_change"  # NEW: Ask if anything needs changing
    SAME_WHAT_CONCERNS = "same_what_concerns"  # NEW: Ask what concerns/solutions
    SAME_EXPLORE_SOLUTIONS = "same_explore_solutions"  # NEW: Explore solutions to concerns
    SAME_NOT_SUCCESSFUL = "same_not_successful"
    SAME_SUCCESSFUL = "same_successful"
    
    # Path 2: Different goals (keeping some + making new)
    DIFFERENT_WHICH_GOALS = "different_which_goals"
    DIFFERENT_KEEPING_AND_NEW = "different_keeping_and_new"
    
    # Path 3: Just creating different goals
    JUST_NEW_GOALS = "just_new_goals"
    REFINE_GOAL = "refine_goal"
    CONFIDENCE_CHECK = "confidence_check"
    LOW_CONFIDENCE = "low_confidence"
    HIGH_CONFIDENCE = "high_confidence"
    MAKE_ACHIEVABLE = "make_achievable"
    
    # Common end states
    REMEMBER_GOAL = "remember_goal"
    MORE_GOALS_CHECK = "more_goals_check"
    END_SESSION = "end_session"


class Session2Manager:
    """Manages conversation flow for Session 2"""
    
    def __init__(self, session1_data: Dict = None, llm_client=None, debug=True):
        self.debug = debug
        self.state = Session2State.GREETINGS
        
        user_name = session1_data.get("user_name") if session1_data else None
        if user_name:
            user_name = user_name.title()
        
        discovery_questions = []
        if session1_data and session1_data.get("goal_details"):
            for goal_info in session1_data["goal_details"]:
                if goal_info.get("discovery_questions"):
                    discovery_questions.extend(goal_info["discovery_questions"])
        
        self.session_data = {
            "user_name": user_name,
            "previous_goals": session1_data.get("goal_details", []) if session1_data else [],
            "discovery_questions": discovery_questions,
            "discovery_responses": [],
            "discovery_question_index": 0,
            "stress_level": None,
            "goal_completion_status": {},
            "successes": [],
            "challenges": [],
            "path_chosen": None,
            "goals_to_keep": [],
            "goals_to_keep_identified": False,
            "new_goals": [],
            "goals_completed_count": 0,
            "current_goal": None,
            "goal_smart_analysis": None,
            "smart_refinement_attempts": 0,
            "confidence_level": None,
            "changes_needed": {},
            "solutions": {},
            "challenges_discussed": False,
            "adjustments_discussed": False,
            "session_start": datetime.now().isoformat(),
            "turn_count": 0,
            "last_coach_response": None,
            "tracking_method_discussed": False,
            "anything_else_asked": False,
            "confidence_asked_for_same_goal": False,
            "questions_asked": set(),
            "final_goodbye_given": False  # NEW: Track if goodbye was given
        }
        self.llm_client = llm_client
        self._log_debug(f"Session initialized with user: {user_name}")
        self._log_debug(f"Discovery questions loaded: {len(discovery_questions)}")
    
    def _log_debug(self, message: str):
        if self.debug:
            print(f"[DEBUG] {message}", flush=True)
    
    def _mark_question_asked(self, question_key: str):
        self.session_data["questions_asked"].add(question_key)
        self._log_debug(f"Marked question asked: {question_key}")
    
    def _has_asked_question(self, question_key: str) -> bool:
        return question_key in self.session_data["questions_asked"]
    
    def set_llm_client(self, llm_client):
        self.llm_client = llm_client
        self._log_debug("LLM client set")
    
    def evaluate_smart_goal(self, goal: str) -> Dict[str, Any]:
        self._log_debug(f"Evaluating SMART goal: '{goal}'")
        
        if not self.llm_client:
            self._log_debug("No LLM client, using heuristic check")
            return self._heuristic_smart_check(goal)
        
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
            is_smart = all(analysis[criterion]["met"] for criterion in ["specific", "measurable", "achievable", "relevant", "timebound"])
            missing = [criterion.upper() for criterion in ["specific", "measurable", "achievable", "relevant", "timebound"] if not analysis[criterion]["met"]]
            
            self._log_debug(f"SMART evaluation result: is_smart={is_smart}, missing={missing}")
            
            return {
                'is_smart': is_smart,
                'analysis': analysis,
                'suggestions': analysis.get('suggestions', ''),
                'missing_criteria': missing
            }
        except Exception as e:
            self._log_debug(f"SMART evaluation error: {e}")
            return self._heuristic_smart_check(goal)
    
    def _heuristic_smart_check(self, goal: str) -> Dict[str, Any]:
        goal_lower = goal.lower()
        has_numbers = bool(re.search(r'\d+', goal))
        time_words = ['day', 'week', 'month', 'daily', 'weekly', 'monthly', 'per week', 'per day', 'times', 'every', 'each', 'by', 'for']
        has_timeframe = any(word in goal_lower for word in time_words)
        action_verbs = ['walk', 'run', 'exercise', 'eat', 'drink', 'sleep', 'reduce', 'increase', 'practice', 'meditate', 'stretch']
        has_action = any(verb in goal_lower for verb in action_verbs)
        vague_words = ['more', 'better', 'less', 'healthier', 'improve']
        has_vague = any(word in goal_lower for word in vague_words)
        
        is_smart = has_numbers and has_timeframe and has_action and not has_vague and len(goal.split()) >= 5
        missing = []
        if not has_action or has_vague: 
            missing.append("SPECIFIC")
        if not has_numbers: 
            missing.append("MEASURABLE")
        if not has_timeframe: 
            missing.append("TIME-BOUND")
        
        return {
            'is_smart': is_smart,
            'analysis': {
                'specific': {'met': has_action and not has_vague, 'issue': 'Use specific action verbs, avoid vague words'},
                'measurable': {'met': has_numbers, 'issue': 'Include specific numbers or quantities'},
                'achievable': {'met': True, 'issue': ''},
                'relevant': {'met': True, 'issue': ''},
                'timebound': {'met': has_timeframe, 'issue': 'Specify frequency or deadline'}
            },
            'suggestions': 'Make it more specific with numbers and a clear timeframe',
            'missing_criteria': missing
        }
    
    def get_state(self) -> Session2State:
        return self.state
    
    def set_state(self, new_state: Session2State):
        old_state = self.state
        self.state = new_state
        self._log_debug(f"STATE TRANSITION: {old_state.value} -> {new_state.value}")
    
    def process_user_input(self, user_input: str, last_coach_response: str = None, 
                          conversation_history: list = None) -> Dict[str, Any]:
        """Process user input and determine state transitions"""
        user_lower = user_input.lower().strip()
        self.session_data["turn_count"] += 1
        
        self._log_debug(f"Processing input in state: {self.state.value}")
        self._log_debug(f"User input: {user_input[:100]}...")
        
        if last_coach_response:
            self.session_data["last_coach_response"] = last_coach_response
        
        result = {
            "next_state": None,
            "context": "",
            "trigger_rag": True
        }
        
        # CRITICAL: If we're in END_SESSION and goodbye was already given, stay there
        if self.state == Session2State.END_SESSION and self.session_data.get("final_goodbye_given"):
            result["context"] = "Session already ended. Politely acknowledge but don't continue conversation."
            result["trigger_rag"] = False
            return result
        
        if self.state == Session2State.GREETINGS:
            if user_input.strip() == "[START_SESSION]":
                result["context"] = f"Welcome {self.session_data.get('user_name', 'them')} back warmly. Keep it brief."
                return result
            
            result["next_state"] = Session2State.CHECK_IN_GOALS
            result["context"] = "Acknowledge briefly. Move to check-in."
            self._mark_question_asked("greeting")
        
        elif self.state == Session2State.CHECK_IN_GOALS:
            result["next_state"] = Session2State.STRESS_LEVEL
            result["context"] = "Acknowledge briefly. Ask stress level (1-10 scale)."
            self._mark_question_asked("check_in")
        
        elif self.state == Session2State.STRESS_LEVEL:
            numbers = re.findall(r'\d+', user_input)
            if numbers:
                stress = int(numbers[0])
                self.session_data["stress_level"] = stress
                self._mark_question_asked("stress_level")
                
                if self.session_data.get("discovery_questions"):
                    result["next_state"] = Session2State.DISCOVERY_QUESTIONS
                    result["context"] = f"Note stress: {stress}/10. Ask ONE discovery question."
                else:
                    result["next_state"] = Session2State.GOAL_COMPLETION
                    result["context"] = f"Note stress: {stress}/10. Ask about goal completion."
            else:
                result["context"] = "Ask for stress level as a number (1-10)."
        
        elif self.state == Session2State.DISCOVERY_QUESTIONS:
            current_q_index = self.session_data["discovery_question_index"]
            if current_q_index < len(self.session_data.get("discovery_questions", [])):
                self.session_data["discovery_responses"].append({
                    "question": self.session_data["discovery_questions"][current_q_index],
                    "response": user_input
                })
                self.session_data["discovery_question_index"] += 1
            
            if self.session_data["discovery_question_index"] < 2 and self.session_data["discovery_question_index"] < len(self.session_data.get("discovery_questions", [])):
                result["context"] = "Acknowledge briefly. Ask ONE more discovery question."
            else:
                result["next_state"] = Session2State.GOAL_COMPLETION
                result["context"] = "Acknowledge. Ask about goal completion."
        
        elif self.state == Session2State.GOAL_COMPLETION:
            self._mark_question_asked("goal_completion")
            result["next_state"] = Session2State.GOALS_FOR_NEXT_WEEK
            result["context"] = "Acknowledge their progress. Ask about next week's goals (same, keep some + add new, or completely new)."
        
        elif self.state == Session2State.GOALS_FOR_NEXT_WEEK:
            same_keywords = ["same", "current", "keep", "continue", "stick", "focusing"]
            add_keywords = ["add", "plus", "also", "another", "new", "and"]
            different_keywords = ["different", "change", "fresh", "switch"]
            
            has_same = any(k in user_lower for k in same_keywords)
            has_add = any(k in user_lower for k in add_keywords)
            has_different = any(k in user_lower for k in different_keywords)
            
            # If they said "add" while on same path, switch to different
            if self.session_data.get("path_chosen") == "same" and has_add:
                self.session_data["path_chosen"] = "different"
                if self.session_data.get("previous_goals"):
                    self.session_data["goals_to_keep"] = [g['goal'] for g in self.session_data["previous_goals"]]
                    self.session_data["goals_to_keep_identified"] = True
                result["next_state"] = Session2State.DIFFERENT_KEEPING_AND_NEW
                result["context"] = "They want to add a new goal. Ask what new goal."
                return result
            
            # First time choosing path
            if not self.session_data.get("path_chosen"):
                # "Keep current and add new" = different path
                if (has_same or has_add) and has_add:
                    self.session_data["path_chosen"] = "different"
                    # Auto-identify they're keeping previous goals
                    if self.session_data.get("previous_goals"):
                        self.session_data["goals_to_keep"] = [g['goal'] for g in self.session_data["previous_goals"]]
                        self.session_data["goals_to_keep_identified"] = True
                    result["next_state"] = Session2State.DIFFERENT_KEEPING_AND_NEW
                    result["context"] = "They want to keep current goals and add new. Ask what new goal."
                # "Same goal only" = same path
                elif has_same and not has_add and not has_different:
                    self.session_data["path_chosen"] = "same"
                    if self.session_data.get("previous_goals"):
                        self.session_data["goals_to_keep"] = [g['goal'] for g in self.session_data["previous_goals"]]
                    result["next_state"] = Session2State.SAME_GOALS_SUCCESSES_CHALLENGES
                    result["context"] = "Keeping same goal. Ask what went well and what was challenging."
                # "Completely new" = new path
                elif has_different and not has_same:
                    self.session_data["path_chosen"] = "new"
                    result["next_state"] = Session2State.JUST_NEW_GOALS
                    result["context"] = "New goals. Ask what they'd like to focus on."
                else:
                    result["context"] = "Clarify: same goal, keep some + add new, or completely new?"
            else:
                result["context"] = "Path already chosen. Continue."
        
        elif self.state == Session2State.SAME_GOALS_SUCCESSES_CHALLENGES:
            if self._has_asked_question("successes_challenges"):
                # They responded to successes/challenges - now ask if anything needs changing
                result["next_state"] = Session2State.SAME_ANYTHING_TO_CHANGE
                result["context"] = "Acknowledge their response briefly (1 sentence). Ask: 'Is there anything about this goal that needs to be changed or worked on?'"
            else:
                # First time - ask the question
                self._mark_question_asked("successes_challenges")
                result["context"] = "Ask: What went well? What was challenging?"
        
        elif self.state == Session2State.SAME_ANYTHING_TO_CHANGE:
            wants_change = any(w in user_lower for w in ["yes", "yeah", "change", "modify", "adjust", "different", "worry", "concerned", "fear", "harder"])
            no_change = any(w in user_lower for w in ["no", "nope", "good", "fine", "keep", "same"])
            
            if wants_change:
                result["next_state"] = Session2State.SAME_WHAT_CONCERNS
                result["context"] = "They want to make changes. Ask what concerns they have or what solutions they're thinking about."
            elif no_change:
                result["next_state"] = Session2State.END_SESSION
                result["context"] = "They're happy with the goal as-is. Give final goodbye."
                self.session_data["final_goodbye_given"] = True
            else:
                result["context"] = "Clarify: Do they want to change anything about their goal? Yes or no?"
        
        elif self.state == Session2State.SAME_WHAT_CONCERNS:
            # They're expressing concerns or proposing solutions
            result["next_state"] = Session2State.SAME_EXPLORE_SOLUTIONS
            result["context"] = "Acknowledge their concerns. Ask what solutions or adjustments they're thinking about."
        
        elif self.state == Session2State.SAME_EXPLORE_SOLUTIONS:
            # Check if they're proposing a specific modification
            has_specific_change = any(word in user_lower for word in ["30", "20", "15", "mins", "minutes", "reduce", "instead", "maybe"])
            
            if has_specific_change:
                self._log_debug("User proposing specific goal modification")
                # Extract the modified goal
                goal_candidate = user_input.strip()
                self.session_data["current_goal"] = goal_candidate
                
                # Add to new goals
                if not self.session_data["new_goals"] or self.session_data["new_goals"][-1] != goal_candidate:
                    self.session_data["new_goals"].append(goal_candidate)
                
                # Evaluate if SMART
                smart_eval = self.evaluate_smart_goal(goal_candidate)
                self.session_data["goal_smart_analysis"] = smart_eval
                self.session_data["smart_refinement_attempts"] = 0
                
                if smart_eval["is_smart"]:
                    result["next_state"] = Session2State.CONFIDENCE_CHECK
                    result["context"] = "Modified goal is SMART! Ask confidence (1-10)."
                else:
                    result["next_state"] = Session2State.REFINE_GOAL
                    result["context"] = f"Modified goal missing: {', '.join(smart_eval['missing_criteria'])}. Help refine it."
            else:
                # Still exploring - help them think through solutions
                result["context"] = "Guide them toward a specific adjustment. What would make it more achievable?"
        
        elif self.state == Session2State.SAME_NOT_SUCCESSFUL:
            result["next_state"] = Session2State.END_SESSION
            result["context"] = "Acknowledge challenges. Encourage. Give final goodbye."
            self.session_data["final_goodbye_given"] = True
        
        elif self.state == Session2State.SAME_SUCCESSFUL:
            result["next_state"] = Session2State.END_SESSION
            result["context"] = "Celebrate success. Give final goodbye."
            self.session_data["final_goodbye_given"] = True
        
        elif self.state == Session2State.DIFFERENT_WHICH_GOALS:
            # Check if we already identified which goals to keep
            if self.session_data.get("goals_to_keep_identified"):
                # Already know which goals - this is them describing the new goal
                result["next_state"] = Session2State.DIFFERENT_KEEPING_AND_NEW
                result["context"] = "Process their new goal idea."
                return result
            
            # First time in this state - identify which goals to keep
            goals_mentioned = []
            for goal_info in self.session_data.get("previous_goals", []):
                goal_text = goal_info['goal'].lower()
                # Check for keywords from the goal
                if any(word in user_lower for word in goal_text.split() if len(word) > 4):
                    goals_mentioned.append(goal_info['goal'])
            
            # Check for "all" or "both" or "current"
            if any(w in user_lower for w in ["all", "both", "current", "same"]):
                goals_mentioned = [g['goal'] for g in self.session_data.get("previous_goals", [])]
            
            if goals_mentioned:
                self.session_data["goals_to_keep"] = goals_mentioned
                self.session_data["goals_to_keep_identified"] = True
                result["next_state"] = Session2State.DIFFERENT_KEEPING_AND_NEW
                result["context"] = f"Noted keeping: {', '.join(goals_mentioned)}. Now ask what new goal they want to add."
            else:
                result["context"] = "Ask which specific previous goals they want to keep."
        
        elif self.state == Session2State.DIFFERENT_KEEPING_AND_NEW:
            goal_candidate = user_input.strip()
            
            # Check if this is a substantial goal description (not just "yes" or single words)
            is_affirmation = user_lower in ["yes", "yeah", "yep", "no", "nope", "ok", "okay"]
            
            if not is_affirmation and len(goal_candidate.split()) > 3:
                self.session_data["current_goal"] = goal_candidate
                
                # Only add to new_goals list if it's not already there
                if not self.session_data["new_goals"] or self.session_data["new_goals"][-1] != goal_candidate:
                    self.session_data["new_goals"].append(goal_candidate)
                
                smart_eval = self.evaluate_smart_goal(goal_candidate)
                self.session_data["goal_smart_analysis"] = smart_eval
                self.session_data["smart_refinement_attempts"] = 0
                
                if smart_eval["is_smart"]:
                    result["next_state"] = Session2State.CONFIDENCE_CHECK
                    result["context"] = "Goal is SMART! Ask confidence (1-10)."
                else:
                    result["next_state"] = Session2State.REFINE_GOAL
                    result["context"] = f"Goal needs refinement. Missing: {', '.join(smart_eval['missing_criteria'])}. Guide them to make it more specific."
            else:
                # Still exploring what the new goal should be - don't add anything to goals list yet
                result["context"] = "Ask what new goal they'd like to add. Get more detail about what they want to focus on."
        
        elif self.state == Session2State.JUST_NEW_GOALS:
            goal_candidate = user_input.strip()
            
            # Check if this is a substantial goal description
            is_affirmation = user_lower in ["yes", "yeah", "yep", "no", "nope", "ok", "okay"]
            
            if not is_affirmation and len(goal_candidate.split()) > 3:
                self.session_data["current_goal"] = goal_candidate
                
                # Only add if it's not already there
                if not self.session_data["new_goals"] or self.session_data["new_goals"][-1] != goal_candidate:
                    self.session_data["new_goals"].append(goal_candidate)
                
                smart_eval = self.evaluate_smart_goal(goal_candidate)
                self.session_data["goal_smart_analysis"] = smart_eval
                self.session_data["smart_refinement_attempts"] = 0
                
                if smart_eval["is_smart"]:
                    result["next_state"] = Session2State.CONFIDENCE_CHECK
                    result["context"] = "Goal is SMART! Ask confidence (1-10)."
                else:
                    result["next_state"] = Session2State.REFINE_GOAL
                    result["context"] = f"Missing: {', '.join(smart_eval['missing_criteria'])}. Guide refinement."
            else:
                # Not a goal yet, keep asking
                result["context"] = "Ask what goal they'd like to focus on."
        
        elif self.state == Session2State.REFINE_GOAL:
            goal_candidate = user_input.strip()
            
            # Check if this is a substantial goal statement (not just "yes" or very short responses)
            is_affirmation = user_lower in ["yes", "yeah", "yep", "no", "nope", "ok", "okay"]
            is_conversational = any(phrase in user_lower for phrase in [
                "i like", "i think", "i feel", "i want to", "i'm feeling",
                "it's a lot", "just ", "that makes sense", "i understand"
            ]) and len(goal_candidate.split()) < 8
            
            if not is_affirmation and not is_conversational and len(goal_candidate.split()) > 5:
                # This might be a goal attempt - evaluate it
                smart_eval = self.evaluate_smart_goal(goal_candidate)
                self.session_data["goal_smart_analysis"] = smart_eval
                self.session_data["smart_refinement_attempts"] += 1
                
                # Only update the goal if it's getting better (more SMART criteria met)
                if smart_eval["is_smart"]:
                    # Goal is SMART - save it and move on
                    self.session_data["current_goal"] = goal_candidate
                    if self.session_data["new_goals"]:
                        self.session_data["new_goals"][-1] = goal_candidate
                    else:
                        self.session_data["new_goals"].append(goal_candidate)
                    
                    result["next_state"] = Session2State.CONFIDENCE_CHECK
                    result["context"] = "Goal is SMART! Ask confidence (1-10)."
                elif self.session_data["smart_refinement_attempts"] >= 3:
                    # Tried 3 times, accept what we have
                    self.session_data["current_goal"] = goal_candidate
                    if self.session_data["new_goals"]:
                        self.session_data["new_goals"][-1] = goal_candidate
                    else:
                        self.session_data["new_goals"].append(goal_candidate)
                    
                    result["next_state"] = Session2State.CONFIDENCE_CHECK
                    result["context"] = "Move to confidence check after 3 attempts."
                else:
                    # Needs more work - update current goal but keep refining
                    self.session_data["current_goal"] = goal_candidate
                    result["context"] = f"Goal still missing: {', '.join(smart_eval['missing_criteria'])}. Ask specific questions to get those details."
            else:
                # This is just a conversational response, keep asking for goal details
                result["context"] = "Continue refining. Ask specific questions to make the goal SMART (numbers, frequency, timeframe)."
        
        elif self.state == Session2State.CONFIDENCE_CHECK:
            # Only look for numbers if we haven't already gotten confidence
            if self.session_data.get("confidence_level") is None:
                numbers = re.findall(r'\d+', user_input)
                if numbers:
                    confidence = int(numbers[0])
                    self.session_data["confidence_level"] = confidence
                    
                    if confidence <= 7:
                        result["next_state"] = Session2State.LOW_CONFIDENCE
                        result["context"] = "Low confidence. Explore what would help increase it."
                    else:
                        is_same = self.session_data.get("path_chosen") == "same"
                        if is_same:
                            result["next_state"] = Session2State.END_SESSION
                            result["context"] = "High confidence! Give final goodbye."
                            self.session_data["final_goodbye_given"] = True
                        else:
                            result["next_state"] = Session2State.REMEMBER_GOAL
                            result["context"] = "High confidence! Ask about tracking method."
                else:
                    result["context"] = "Ask for confidence as a number (1-10). Be clear and direct."
            else:
                # Already have confidence, they're just responding - move forward
                confidence = self.session_data["confidence_level"]
                if confidence <= 7:
                    result["next_state"] = Session2State.LOW_CONFIDENCE
                    result["context"] = "Explore what would help."
                else:
                    result["next_state"] = Session2State.REMEMBER_GOAL
                    result["context"] = "Ask about tracking method."
        
        elif self.state == Session2State.LOW_CONFIDENCE:
            result["next_state"] = Session2State.MAKE_ACHIEVABLE
            result["context"] = "Explore what would make it achievable."
        
        elif self.state == Session2State.HIGH_CONFIDENCE:
            result["next_state"] = Session2State.REMEMBER_GOAL
            result["context"] = "Ask about tracking."
        
        elif self.state == Session2State.MAKE_ACHIEVABLE:
            is_same = self.session_data.get("path_chosen") == "same"
            if is_same:
                result["next_state"] = Session2State.END_SESSION
                result["context"] = "Acknowledge adjustments. Give final goodbye."
                self.session_data["final_goodbye_given"] = True
            else:
                result["next_state"] = Session2State.REMEMBER_GOAL
                result["context"] = "Ask about tracking."
        
        elif self.state == Session2State.REMEMBER_GOAL:
            result["next_state"] = Session2State.MORE_GOALS_CHECK
            result["context"] = "Acknowledge tracking. Ask if they want another goal."
        
        elif self.state == Session2State.MORE_GOALS_CHECK:
            wants_more = any(w in user_lower for w in ["yes", "yeah", "another", "more", "add"])
            done = any(w in user_lower for w in ["no", "nope", "done", "good", "enough"])
            
            if wants_more:
                self.session_data["current_goal"] = None
                self.session_data["smart_refinement_attempts"] = 0
                result["next_state"] = Session2State.JUST_NEW_GOALS
                result["context"] = "Ask what other goal."
            else:
                result["next_state"] = Session2State.END_SESSION
                result["context"] = "Give final goodbye for Session 2."
                self.session_data["final_goodbye_given"] = True
        
        elif self.state == Session2State.END_SESSION:
            # Already in END_SESSION, just acknowledge politely
            result["context"] = "Session already complete. Politely acknowledge but don't extend conversation."
            result["trigger_rag"] = False
        
        if result["next_state"]:
            self._log_debug(f"Next state will be: {result['next_state'].value}")
        
        return result
    
    def get_system_prompt_addition(self) -> str:
        """Get state-specific system prompt additions"""
        
        previous_goals_text = ""
        if self.session_data.get("previous_goals"):
            if len(self.session_data["previous_goals"]) == 1:
                previous_goals_text = f"\nTheir previous goal: \"{self.session_data['previous_goals'][0]['goal']}\""
            else:
                previous_goals_text = f"\nTheir previous goals:"
                for i, g in enumerate(self.session_data["previous_goals"], 1):
                    previous_goals_text += f"\n  {i}. \"{g['goal']}\""
        
        session_context = ""
        if self.session_data.get("stress_level"):
            session_context += f"\nStress level: {self.session_data['stress_level']}/10"
        
        if self.session_data.get("goals_to_keep"):
            session_context += f"\nGoals keeping: {', '.join(self.session_data['goals_to_keep'])}"
        
        if self.session_data.get("new_goals"):
            session_context += f"\nNew goals set: {len(self.session_data['new_goals'])}"
        
        prompts = {
            Session2State.GREETINGS: f"""
Welcome {self.session_data.get('user_name', 'them')} back to Session 2.

Be warm and brief. Just say hi and ask how their week was.
NO markdown, emojis, or extra questions.
{previous_goals_text}""",
            
            Session2State.CHECK_IN_GOALS: f"""
Ask about their goal from last week.
{previous_goals_text}

CRITICAL: Ask ONLY about how it went with their goal. ONE question.
NO stress questions, NO other topics.
Example: "How did it go with [goal]?"
{session_context}""",
            
            Session2State.STRESS_LEVEL: f"""
Ask ONLY about stress level (1-10).

"On a scale of 1 to 10, how stressed were you this week?"

CRITICAL: Do NOT ask about their goals, challenges, or anything else. Just stress level.
{session_context}""",
            
            Session2State.DISCOVERY_QUESTIONS: f"""
Ask ONE discovery question.
Available: {', '.join(self.session_data.get('discovery_questions', [])[:3])}

Pick most relevant. Be conversational.
{session_context}""",
            
            Session2State.GOAL_COMPLETION: f"""
Ask about goal completion.

CRITICAL: Ask this ONCE. Accept their answer. Do NOT ask follow-up questions about details.
Example: "Did you complete your goal?"
{session_context}""",
            
            Session2State.GOALS_FOR_NEXT_WEEK: f"""
Ask what they want to focus on next week.

Three options:
1. Same goal as last week
2. Keep that goal AND add a new one  
3. Completely new goals

Be clear and simple.
{session_context}""",
            
            Session2State.SAME_GOALS_SUCCESSES_CHALLENGES: f"""
They're keeping the same goal.

FIRST response (when you haven't asked yet): Acknowledge their choice briefly (1 sentence), then ask: "What went well this week? What was challenging?"

SECOND response (after they answer): Acknowledge what they shared in 1-2 sentences. DO NOT ask follow-up questions. DO NOT ask about modifying goals. DO NOT explore further. Just acknowledge and validate.

CRITICAL: 
- NO questions about stress, confidence, modifications, or next steps
- NO exploring challenges in depth
- Just brief acknowledgment (1-2 sentences max)
- If they mention wanting to change something, acknowledge it but let them lead
{session_context}""",
            
            Session2State.SAME_NOT_SUCCESSFUL: f"""
They had challenges.

Empathize briefly (1-2 sentences). Be encouraging.
{session_context}""",
            
            Session2State.SAME_SUCCESSFUL: f"""
They succeeded!

Celebrate briefly (1-2 sentences).
{session_context}""",
            
            Session2State.DIFFERENT_WHICH_GOALS: f"""
They want to keep some goals and add new ones.

FIRST TIME: Ask which of their previous goals they want to keep.
{previous_goals_text}

AFTER IDENTIFIED: They're describing their new goal idea - transition to asking for specifics.

Be conversational.
{session_context}""",
            
            Session2State.DIFFERENT_KEEPING_AND_NEW: f"""
They're adding a new goal while keeping previous ones.

Goals they're keeping:
{chr(10).join(f'  - {g}' for g in self.session_data.get('goals_to_keep', [])) if self.session_data.get('goals_to_keep') else '  - (identifying)'}

If they haven't stated a clear new goal yet: Ask "What new goal would you like to add?"

If they've stated a general idea but it's not SMART yet: Guide them to make it specific with numbers and timeframe.

CRITICAL: Help them turn vague ideas into SMART goals. Ask clarifying questions to get:
- Specific action
- Measurable amount (how much, how many, how long)
- Timeframe (how often, which days)
{session_context}""",
            
            Session2State.JUST_NEW_GOALS: f"""
Ask about new goal.

"What would you like to focus on?"
{session_context}""",
            
            Session2State.REFINE_GOAL: f"""
Goal needs refinement to be SMART.

Current goal attempt: {self.session_data.get('current_goal')}
Missing criteria: {', '.join((self.session_data.get('goal_smart_analysis') or {}).get('missing_criteria', []))}
Refinement attempts: {self.session_data.get('smart_refinement_attempts', 0)}/3

CRITICAL: Your job is ONLY to help refine the goal. DO NOT ask about confidence yet.

Ask specific questions to get missing information:
- If missing SPECIFIC: "What exactly will you do?"
- If missing MEASURABLE: "How much/many? How long?"
- If missing TIMEBOUND: "How often? Which days? When?"

Keep questions simple and focused. One question at a time.

Once they give you all the details, the system will move to confidence check automatically.
{session_context}""",
            
            Session2State.CONFIDENCE_CHECK: f"""
Ask about confidence level.

Current goal: {self.session_data.get('current_goal')}

CRITICAL: Ask ONLY about confidence. Do NOT ask about other topics.

"On a scale of 1 to 10, how confident are you that you can achieve this goal?"

Wait for a number. Don't explore or discuss until they give you the confidence rating.
{session_context}""",
            
            Session2State.LOW_CONFIDENCE: f"""
Low confidence. Explore what would help.
{session_context}""",
            
            Session2State.HIGH_CONFIDENCE: f"""
High confidence! Celebrate.
{session_context}""",
            
            Session2State.MAKE_ACHIEVABLE: f"""
Help make goal more achievable.
{session_context}""",
            
            Session2State.REMEMBER_GOAL: f"""
Ask how they'll remember/track the goal.
{session_context}""",
            
            Session2State.MORE_GOALS_CHECK: f"""
Ask: "Would you like to set another goal?"

Simple yes/no question.
{session_context}""",
            
            Session2State.END_SESSION: f"""
FINAL GOODBYE FOR SESSION 2.

CRITICAL INSTRUCTIONS:
- This is the FINAL message of Session 2
- DO NOT ask any questions
- DO NOT ask "Is there anything else?"
- DO NOT prompt for more conversation
- Give a warm, conclusive goodbye

Your goals for next week:
{chr(10).join(f'  - {g}' for g in (self.session_data.get('goals_to_keep', []) + self.session_data.get('new_goals', []))) or '  - (continuing previous goals)'}

Say something like:
"Great work today, {self.session_data.get('user_name', '')}! You'll be working on [briefly mention their goal(s)]. I'll see you next week at Session 3. Take care!"

Keep it to 2-3 sentences maximum. End definitively.
{session_context}"""
        }
        
        return prompts.get(self.state, f"Current state: {self.state.value}{session_context}")
    
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
        
        # Convert set to list for JSON serialization
        session_data_copy = self.session_data.copy()
        if isinstance(session_data_copy.get("questions_asked"), set):
            session_data_copy["questions_asked"] = list(session_data_copy["questions_asked"])
        
        data = {
            "state": self.state.value,
            "session_data": session_data_copy,
            "conversation_history": conversation_history or []
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        self._log_debug(f"Session saved to {filename}")
        return filename
    
    def load_session(self, filename: str):
        """Load session data from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.state = Session2State(data["state"])
        self.session_data = data["session_data"]
        
        if isinstance(self.session_data.get("questions_asked"), list):
            self.session_data["questions_asked"] = set(self.session_data["questions_asked"])
        
        self._log_debug(f"Session loaded from {filename}")
        
        return data.get("conversation_history", [])