from enum import Enum
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
import re

# Utilities
from utils.smart_evaluation import evaluate_smart_goal_with_llm, heuristic_smart_check, create_concise_goal
from utils.unified_storage import save_unified_session, get_active_goals, extract_user_profile
from utils.state_prompts import get_session4_prompt
from utils.state_helpers import (
    create_state_result,
    check_affirmative,
    check_negative,
    extract_number,
    check_wants_more,
    check_done
)
from utils.goal_detection import is_likely_goal
from utils.database import save_session_to_db, load_session_from_db

class Session4State(Enum):
    """States for Session 4 conversation flow"""
    GREETINGS = "greetings"
    REINFORCE_GOAL_FROM_LAST_SESSION = "reinforce_goal_from_last_session"
    CHECK_IN_GOALS = "check_in_goals"
    
    # Path 1: Goals achieved
    WHAT_HAPPENED = "what_happened"
    WHAT_CAN_BE_DONE_TO_MAKE_IT_BETTER = "what_can_be_done_to_make_it_better"
    
    # Path 2: Goals not achieved - Stress handling
    STRESS_LEVEL = "stress_level"
    STRESS_HIGH_WHAT_HAPPENED = "stress_high_what_happened"
    STRESS_HIGH_ANYTHING_WE_CAN_TALK_ABOUT = "stress_high_anything_we_can_talk_about"
    STRESS_LOW_WHAT_HAPPENED = "stress_low_what_happened"
    
    # Focus selection
    WHATS_THE_FOCUS_TODAY = "whats_the_focus_today"
    
    # Path A: Current goals (keeping existing)
    CURRENT_GOALS_ANYTHING_NEEDING_TO_CHANGE = "current_goals_anything_needing_to_change"
    
    # Path B: New goals
    NEW_GOALS_SMART_CHECK = "new_goals_smart_check"
    SMART_YES_PATH = "smart_yes_path"
    SMART_NO_PATH = "smart_no_path"
    
    # Common states
    CONFIDENCE_CHECK = "confidence_check"
    LOW_CONFIDENCE_WHAT_SUCCESSES = "low_confidence_what_successes"
    LOW_CONFIDENCE_HOW_CAN_WE_MAKE_IT_MORE_ACHIEVABLE = "low_confidence_how_can_we_make_it_more_achievable"
    HIGH_CONFIDENCE_PATH = "high_confidence_path"
    
    # Tracking and closing
    HOW_WILL_YOU_REMEMBER_TO_DO_YOUR_GOAL = "how_will_you_remember_to_do_your_goal"
    # REMOVED: HOW_WILL_YOU_CONTINUE_YOUR_GOALS
    ANY_FINAL_QUESTIONS = "any_final_questions"
    END_SESSION = "end_session"


class Session4Manager:
    """Manages conversation flow for Session 4"""
    
    def __init__(self, user_profile: Dict = None, llm_client=None, debug=True):
        self.debug = debug
        self.state = Session4State.GREETINGS
        
        # Extract from unified profile
        self.uid = user_profile.get("uid") if user_profile else None
        user_name = user_profile.get("name") if user_profile else None
        if user_name:
            user_name = user_name.title()
        
        # Get active goals from previous session
        previous_goals = []
        discovery_info = {}
        if user_profile:
            # Get active goals
            all_goals = user_profile.get("goals", [])
            active_goals = get_active_goals(all_goals)
            previous_goals = [{
                "goal": g["goal"],
                "confidence": g["confidence"],
                "session_created": g.get("session_created", 3)
            } for g in active_goals]
            
            # Get discovery info
            discovery_info = user_profile.get("discovery_questions", {})
        
        self.session_data = {
            "uid": self.uid,
            "user_name": user_name,
            "previous_goals": previous_goals,
            "discovery_info": discovery_info,
            "stress_level": None,
            "goals_achieved": None,  # True/False/None
            "what_happened": None,
            "improvements_discussed": False,
            "path_chosen": None,  # "current" or "new"
            "goals_to_keep": [],
            "new_goals": [],
            "current_goal": None,
            "goal_smart_analysis": None,
            "smart_refinement_attempts": 0,
            "confidence_level": None,
            "changes_needed": {},
            "tracking_method": None,
            "session_start": datetime.now().isoformat(),
            "turn_count": 0,
            "last_coach_response": None,
            "questions_asked": set(),
            "final_goodbye_given": False
        }
        self.llm_client = llm_client
        self._log_debug(f"Session 4 initialized with user: {user_name}, UID: {self.uid}")
        self._log_debug(f"Previous goals loaded: {len(previous_goals)}")
    
    def _create_concise_goal(self, full_goal: str) -> str:
        """Create a concise version of the goal for storage"""
        return create_concise_goal(full_goal)
    
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
        """Use LLM to evaluate if a goal is SMART"""
        self._log_debug(f"Evaluating SMART goal: '{goal}'")
        
        if not self.llm_client:
            self._log_debug("No LLM client, using heuristic check")
            return heuristic_smart_check(goal)
        
        try:
            result = evaluate_smart_goal_with_llm(goal, self.llm_client)
            self._log_debug(f"SMART evaluation result: is_smart={result['is_smart']}, missing={result['missing_criteria']}")
            return result
        except Exception as e:
            self._log_debug(f"SMART evaluation error: {e}")
            return heuristic_smart_check(goal)
    
    def get_state(self) -> Session4State:
        return self.state
    
    def set_state(self, new_state: Session4State):
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
        
        result = create_state_result()
        
        # If session ended, stay in END_SESSION
        if self.state == Session4State.END_SESSION and self.session_data.get("final_goodbye_given"):
            result["context"] = "Session already ended. Politely acknowledge but don't continue conversation."
            result["trigger_rag"] = False
            return result
        
        # GREETINGS
        if self.state == Session4State.GREETINGS:
            if user_input.strip() == "[START_SESSION]":
                result["context"] = f"Welcome {self.session_data.get('user_name', 'them')} to Session 4. Keep it brief and warm."
                return result
            
            result["next_state"] = Session4State.REINFORCE_GOAL_FROM_LAST_SESSION
            result["context"] = "Acknowledge briefly. Move to reinforcing goals from last session."
            self._mark_question_asked("greeting")
        
        # REINFORCE GOAL FROM LAST SESSION
        elif self.state == Session4State.REINFORCE_GOAL_FROM_LAST_SESSION:
            # Check if they're already telling us they achieved goals
            achievement_phrases = ["hit both", "achieved both", "did both", "completed both", 
                                "yes", "yup", "yeah", "both", "all"]
            if any(phrase in user_lower for phrase in achievement_phrases):
                self.session_data["goals_achieved"] = True
                result["next_state"] = Session4State.WHAT_HAPPENED
                result["context"] = "Great! They achieved goals. Ask: 'That's fantastic! What happened that made it work so well for you?'"
            else:
                result["next_state"] = Session4State.CHECK_IN_GOALS
                result["context"] = "Acknowledge briefly. Ask: 'How did achieving those goals go this week?'"

        # CHECK IN GOALS
        elif self.state == Session4State.CHECK_IN_GOALS:
            # First time in this state - ask the question
            if not self._has_asked_question("check_in_goals"):
                self._mark_question_asked("check_in_goals")
                result["context"] = "Ask: 'How did it go with your goals this past week?'"
                return result
            
            # Detect if goals were achieved
            positive_indicators = ["yes", "great", "good", "achieved", "completed", "did it", "success", 
                                "both", "all", "accomplished", "hit", "met", "well", "worked"]
            negative_indicators = ["no", "not really", "didn't", "couldn't", "failed", "hard", 
                                "difficult", "missed", "partially", "one", "only one"]
            
            # Check for explicit statements
            explicit_yes = any(phrase in user_lower for phrase in ["hit both", "achieved both", "did both", "both goals", "all goals"])
            explicit_no = any(phrase in user_lower for phrase in ["didn't hit", "missed", "only hit one", "couldn't do"])
            
            has_positive = any(word in user_lower for word in positive_indicators)
            has_negative = any(word in user_lower for word in negative_indicators)
            
            # Log what we detected
            self._log_debug(f"Positive indicators: {has_positive}, Negative indicators: {has_negative}")
            self._log_debug(f"Explicit yes: {explicit_yes}, Explicit no: {explicit_no}")
            
            # If they explicitly said they hit goals
            if explicit_yes or "hit both" in user_lower:
                self.session_data["goals_achieved"] = True
                result["next_state"] = Session4State.WHAT_HAPPENED
                result["context"] = "Goals were achieved! Ask: 'What happened that made it work so well for you this week?'"
            elif explicit_no:
                self.session_data["goals_achieved"] = False
                result["next_state"] = Session4State.STRESS_LEVEL
                result["context"] = "Goals weren't achieved. Ask: 'On a scale of 1-10, what was your stress level this past week?'"
            elif has_positive and not has_negative:
                self.session_data["goals_achieved"] = True
                result["next_state"] = Session4State.WHAT_HAPPENED
                result["context"] = "Goals were achieved! Ask: 'What happened that made it work so well for you this week?'"
            elif has_negative and not has_positive:
                self.session_data["goals_achieved"] = False
                result["next_state"] = Session4State.STRESS_LEVEL
                result["context"] = "Goals weren't achieved. Ask: 'On a scale of 1-10, what was your stress level this past week?'"
            else:
                # Ambiguous - ask for direct clarification
                clarification_count = self.session_data.get('check_in_clarification_count', 0)
                self.session_data['check_in_clarification_count'] = clarification_count + 1
                
                if clarification_count >= 2:
                    # After 2 attempts, assume positive if they're still engaged
                    self.session_data["goals_achieved"] = True
                    result["next_state"] = Session4State.WHAT_HAPPENED
                    result["context"] = "Move forward assuming goals were achieved. Ask: 'What helped you stay on track this week?'"
                else:
                    result["context"] = "Not clear if goals were achieved. Ask directly: 'Were you able to complete both of your goals this week - the sleep routine and the walks?'"

        # WHAT HAPPENED (goals achieved path)
        elif self.state == Session4State.WHAT_HAPPENED:
            self.session_data["what_happened"] = user_input
            result["next_state"] = Session4State.WHAT_CAN_BE_DONE_TO_MAKE_IT_BETTER
            result["context"] = "Acknowledge their success. Ask what can be done to make things even better."
                

        # WHAT CAN BE DONE TO MAKE IT BETTER
        elif self.state == Session4State.WHAT_CAN_BE_DONE_TO_MAKE_IT_BETTER:
            self.session_data["improvements_discussed"] = True
            
            # Check if they're describing specific changes/adjustments
            change_indicators = ["increase", "decrease", "more", "less", "up", "down", "adjust", 
                                "change", "bump", "add", "different"]
            has_change = any(word in user_lower for word in change_indicators)
            
            # Check if they want to keep things the same
            keep_indicators = ["keep", "same", "continue", "maintaining", "stay", "just keep"]
            has_keep = any(phrase in user_lower for phrase in keep_indicators)
            
            if has_change and is_likely_goal(user_input):
                # They're describing a specific change to their goal
                self.session_data["path_chosen"] = "current"
                self.session_data["changes_needed"]["has_changes"] = True
                self.session_data["changes_needed"]["description"] = user_input
                result["next_state"] = Session4State.CONFIDENCE_CHECK
                result["context"] = "Acknowledge the change briefly. Ask: 'On a scale of 1-10, how confident are you about achieving this adjusted goal?'"
            elif has_keep:
                # They want to keep current goals as-is
                self.session_data["path_chosen"] = "current"
                result["next_state"] = Session4State.CURRENT_GOALS_ANYTHING_NEEDING_TO_CHANGE
                result["context"] = "They want to continue current goals. Ask: 'Is there anything that needs to change with your current goals, or are you good with keeping them as they are?'"
            else:
                # Move to focus selection to clarify
                result["next_state"] = Session4State.WHATS_THE_FOCUS_TODAY
                result["context"] = "Acknowledged improvements. Ask: 'Would you like to continue working on these same goals, or would you prefer to set new goals for yourself?'"
        
        
        # STRESS LEVEL (goals not achieved path)
        elif self.state == Session4State.STRESS_LEVEL:
            stress = extract_number(user_input)
            if stress and 1 <= stress <= 10:
                self.session_data["stress_level"] = stress
                if stress >= 7:
                    result["next_state"] = Session4State.STRESS_HIGH_WHAT_HAPPENED
                    result["context"] = f"High stress ({stress}/10). Ask what happened with empathy."
                else:
                    result["next_state"] = Session4State.STRESS_LOW_WHAT_HAPPENED
                    result["context"] = f"Lower stress ({stress}/10). Ask what happened with their goals."
                self._mark_question_asked("stress_level")
            else:
                result["context"] = "Didn't get valid stress level (1-10). Ask: 'On a scale of 1-10, what was your stress level this past week?'"
        
        # STRESS HIGH - WHAT HAPPENED
        elif self.state == Session4State.STRESS_HIGH_WHAT_HAPPENED:
            self.session_data["what_happened"] = user_input
            result["next_state"] = Session4State.STRESS_HIGH_ANYTHING_WE_CAN_TALK_ABOUT
            result["context"] = "Acknowledge their challenges. Ask if there's anything they'd like to discuss."
        
        # STRESS HIGH - ANYTHING WE CAN TALK ABOUT
        elif self.state == Session4State.STRESS_HIGH_ANYTHING_WE_CAN_TALK_ABOUT:
            result["next_state"] = Session4State.WHATS_THE_FOCUS_TODAY
            result["context"] = "Provide support. Move to focus selection."
        
        # STRESS LOW - WHAT HAPPENED
        elif self.state == Session4State.STRESS_LOW_WHAT_HAPPENED:
            self.session_data["what_happened"] = user_input
            result["next_state"] = Session4State.WHATS_THE_FOCUS_TODAY
            result["context"] = "Acknowledge what happened. Move to focus selection."
        
      # WHAT'S THE FOCUS TODAY
        elif self.state == Session4State.WHATS_THE_FOCUS_TODAY:
            # First, check if we already chose a path and they're now providing a new goal
            if self.session_data.get("path_chosen") == "new" and is_likely_goal(user_input):
                self.session_data["current_goal"] = user_input
                
                # Evaluate if SMART
                smart_result = self.evaluate_smart_goal(user_input)
                self.session_data["goal_smart_analysis"] = smart_result
                
                if smart_result["is_smart"]:
                    result["next_state"] = Session4State.SMART_YES_PATH
                    result["context"] = "Goal is SMART. Acknowledge and move forward."
                else:
                    result["next_state"] = Session4State.SMART_NO_PATH
                    result["context"] = f"Goal is not SMART. Missing: {', '.join(smart_result['missing_criteria'])}. Help refine it."
                return result
            
            # Check if they've already discussed changes (coming from WHAT_CAN_BE_DONE_TO_MAKE_IT_BETTER)
            # and are now confirming details or providing confidence
            came_from_improvements = self.session_data.get("improvements_discussed", False)
            confidence_num = extract_number(user_input)
            is_confidence = confidence_num and 0 <= confidence_num <= 10
            
            # Check if they're confirming goal details (e.g., "2 days seems good")
            confirming_indicators = ["good", "fine", "yes", "perfect", "right", "correct", "keep", "stay"]
            is_confirming = any(word in user_lower for word in confirming_indicators)
            
            if came_from_improvements and is_confidence:
                # They gave us confidence after discussing changes - treat as current goals path
                self.session_data["path_chosen"] = "current"
                self.session_data["confidence_level"] = confidence_num
                self.session_data["changes_needed"]["has_changes"] = True
                self._mark_question_asked("confidence_check")
                
                if confidence_num < 7:
                    result["next_state"] = Session4State.LOW_CONFIDENCE_WHAT_SUCCESSES
                    result["context"] = f"Confidence noted ({confidence_num}/10). Explore successes to build confidence."
                else:
                    result["next_state"] = Session4State.HIGH_CONFIDENCE_PATH
                    result["context"] = f"High confidence ({confidence_num}/10)! Move forward to tracking."
                return result
            
            if came_from_improvements and is_confirming:
                # They're confirming goal details after discussing improvements
                # Continue the conversation naturally, ask about confidence
                result["context"] = "Acknowledge their confirmation. Ask: 'On a scale of 1-10, how confident are you feeling about sticking with these goals?'"
                return result
            
            # Detect if they want to keep current goals or create new ones
            current_indicators = ["current", "same", "keep", "continue", "existing", "maintaining", "focus", "working"]
            new_indicators = ["new", "different", "something else"]
            
            has_current = any(word in user_lower for word in current_indicators)
            has_new = any(word in user_lower for word in new_indicators)
            
            # Check for phrases that indicate modifying current goals
            modify_indicators = ["challenge", "more", "increase", "add", "adjust", "bump", "up", "raise"]
            has_modify = any(word in user_lower for word in modify_indicators)
            
            if has_current and not has_new:
                self.session_data["path_chosen"] = "current"
                # Don't ask about changes if they already described them in previous state
                if self.session_data.get("changes_needed", {}).get("description"):
                    result["next_state"] = Session4State.CONFIDENCE_CHECK
                    result["context"] = "Confirm the change briefly. Ask: 'On a scale of 1-10, how confident are you about achieving this adjusted goal?'"
                else:
                    result["next_state"] = Session4State.CURRENT_GOALS_ANYTHING_NEEDING_TO_CHANGE
                    result["context"] = "They chose current goals. Ask: 'Is there anything that needs to change with your current goals to help you be successful?'"
                self._mark_question_asked("focus_selection")
            elif has_new and not has_current:
                self.session_data["path_chosen"] = "new"
                # Don't transition yet - wait for them to provide the goal
                result["context"] = "They want new goals. Ask: 'What would you like to focus on?'"
                self._mark_question_asked("focus_selection")
            elif has_modify or (has_current and has_new):
                # They want to modify current goals - this should go to CONFIDENCE_CHECK after confirming
                self.session_data["path_chosen"] = "current"
                self.session_data["changes_needed"]["has_changes"] = True
                self.session_data["changes_needed"]["description"] = user_input
                result["next_state"] = Session4State.CONFIDENCE_CHECK  # <-- CHANGE THIS
                result["context"] = "Acknowledge the adjustment (e.g., 'Adding one more day to 4 days a week sounds great'). Ask: 'On a scale of 1-10, how confident are you about achieving this adjusted goal?'"
                self._mark_question_asked("focus_selection")
            else:
                # Ambiguous - clarify
                result["context"] = "Not clear which path they want. Ask directly: 'Would you like to continue working on your current goals, or would you prefer to set completely new goals?'"
    
        # CURRENT GOALS - ANYTHING NEEDING TO CHANGE
        elif self.state == Session4State.CURRENT_GOALS_ANYTHING_NEEDING_TO_CHANGE:
            # First time: ask the question
            if not self._has_asked_question("anything_to_change"):
                self._mark_question_asked("anything_to_change")
                result["context"] = "Ask: 'Is there anything that needs to change with your current goals to help you be successful?'"
                return result
            
            # Process their response
            # Check if they've explicitly said no changes or confirmed they're keeping same
            no_change_indicators = ["no", "same", "keep", "good", "fine", "ready", "nothing"]
            has_no_change = any(word in user_lower for word in no_change_indicators)
            
            # Check for explicit change indicators
            change_indicators = ["yes", "change", "adjust", "modify", "increase", "decrease", "more", "less", "challenge"]
            has_change = any(word in user_lower for word in change_indicators)
            
            # Check if this is a confidence number (0-10)
            confidence_check = extract_number(user_input)
            is_confidence = confidence_check and 0 <= confidence_check <= 10
            
            # Check if user is describing a modification (longer response with goal details)
            is_describing_change = len(user_input.split()) > 5 and any(word in user_lower for word in ["want", "going", "planning", "will"])
            
            # Count how many exchanges we've had in this state
            change_discussion_count = self.session_data.get('change_discussion_count', 0)
            self.session_data['change_discussion_count'] = change_discussion_count + 1
            
            if is_confidence:
                # They jumped straight to confidence - accept it
                self.session_data["confidence_level"] = confidence_check
                self.session_data["changes_needed"]["has_changes"] = False  # Assume no changes if they skipped to confidence
                if confidence_check < 7:
                    result["next_state"] = Session4State.LOW_CONFIDENCE_WHAT_SUCCESSES
                    result["context"] = f"Confidence noted ({confidence_check}/10). Explore successes to build confidence."
                else:
                    result["next_state"] = Session4State.HIGH_CONFIDENCE_PATH
                    result["context"] = f"High confidence ({confidence_check}/10)! Move forward to tracking."
                self._mark_question_asked("confidence_check")
            elif has_change or is_describing_change:
                # They want to make changes
                self.session_data["changes_needed"]["has_changes"] = True
                
                if is_describing_change:
                    # They're already describing the change - acknowledge and move to confidence
                    self.session_data["changes_needed"]["description"] = user_input
                    result["next_state"] = Session4State.CONFIDENCE_CHECK
                    result["context"] = f"Acknowledge their change briefly (1 sentence). Then ask: 'On a scale of 1-10, how confident are you about achieving this adjusted goal?'"
                elif change_discussion_count >= 2:
                    # We've discussed changes enough - move to confidence
                    result["next_state"] = Session4State.CONFIDENCE_CHECK
                    result["context"] = "Changes discussed. Ask: 'On a scale of 1-10, how confident are you about achieving these goals?'"
                else:
                    # Continue exploring what they want to change
                    result["context"] = "Acknowledge their desire to change. Ask: 'What would you like to adjust?'"
            elif has_no_change or check_negative(user_input):
                # No changes needed - move to confidence check
                self.session_data["changes_needed"]["has_changes"] = False
                result["next_state"] = Session4State.CONFIDENCE_CHECK
                result["context"] = "No changes needed. Ask: 'On a scale of 1-10, how confident are you about achieving these goals?'"
            elif change_discussion_count >= 3:
                # Too many exchanges - force transition to confidence
                self.session_data["changes_needed"]["has_changes"] = True
                result["next_state"] = Session4State.CONFIDENCE_CHECK
                result["context"] = "Acknowledge what they've shared. Ask: 'On a scale of 1-10, how confident are you about achieving these goals?'"
            else:
                # Continue discussing - but guide toward a decision
                if change_discussion_count >= 2:
                    result["context"] = "Continue briefly, then ask: 'On a scale of 1-10, how confident are you about achieving these goals?'"
                else:
                    result["context"] = "Listen to their thoughts on potential changes. Guide them toward clarity on what they want to adjust."
        
        # NEW GOALS - SMART YES PATH
        elif self.state == Session4State.SMART_YES_PATH:
            # Add to new goals
            if self.session_data.get("current_goal"):
                self.session_data["new_goals"].append(self.session_data["current_goal"])
                self.session_data["current_goal"] = None  # Clear for next potential goal
            
            result["next_state"] = Session4State.CONFIDENCE_CHECK
            result["context"] = "Goal accepted and is SMART. Acknowledge briefly. Move to confidence check."

        # NEW GOALS - SMART NO PATH
        elif self.state == Session4State.SMART_NO_PATH:
            # Check if they refined the goal
            if is_likely_goal(user_input):
                self.session_data["current_goal"] = user_input
                self.session_data["smart_refinement_attempts"] += 1
                
                # Re-evaluate
                smart_result = self.evaluate_smart_goal(user_input)
                self.session_data["goal_smart_analysis"] = smart_result
                
                if smart_result["is_smart"] or self.session_data["smart_refinement_attempts"] >= 3:
                    # Accept after 3 attempts or if now SMART
                    self.session_data["new_goals"].append(user_input)
                    self.session_data["current_goal"] = None
                    result["next_state"] = Session4State.CONFIDENCE_CHECK
                    result["context"] = "Goal refined and accepted. Move to confidence check."
                else:
                    result["context"] = f"Still needs work. Missing: {', '.join(smart_result['missing_criteria'])}. Help refine with specific questions."
            else:
                result["context"] = "Encourage them to refine their goal. Ask specific questions about what's missing to make it SMART."
        # SMART YES PATH
        elif self.state == Session4State.SMART_YES_PATH:
            # Add to new goals
            if self.session_data.get("current_goal"):
                self.session_data["new_goals"].append(self.session_data["current_goal"])
            
            result["next_state"] = Session4State.CONFIDENCE_CHECK
            result["context"] = "Goal accepted. Move to confidence check."
        
        # SMART NO PATH
        elif self.state == Session4State.SMART_NO_PATH:
            # Check if they refined the goal
            if is_likely_goal(user_input):
                self.session_data["current_goal"] = user_input
                self.session_data["smart_refinement_attempts"] += 1
                
                # Re-evaluate
                smart_result = self.evaluate_smart_goal(user_input)
                self.session_data["goal_smart_analysis"] = smart_result
                
                if smart_result["is_smart"] or self.session_data["smart_refinement_attempts"] >= 2:
                    # Accept after 2 attempts or if now SMART
                    self.session_data["new_goals"].append(user_input)
                    result["next_state"] = Session4State.CONFIDENCE_CHECK
                    result["context"] = "Goal refined and accepted. Move to confidence check."
                else:
                    result["context"] = f"Still missing: {', '.join(smart_result['missing_criteria'])}. Help refine further."
            else:
                result["context"] = "Encourage them to refine their goal to be SMART."
        
        # CONFIDENCE CHECK
        elif self.state == Session4State.CONFIDENCE_CHECK:
            confidence = extract_number(user_input)
            if confidence and 1 <= confidence <= 10:
                self.session_data["confidence_level"] = confidence
                if confidence < 7:
                    result["next_state"] = Session4State.LOW_CONFIDENCE_WHAT_SUCCESSES
                    result["context"] = f"Low confidence ({confidence}/10). Explore successes."
                else:
                    result["next_state"] = Session4State.HIGH_CONFIDENCE_PATH
                    result["context"] = f"Good confidence ({confidence}/10). Move forward."
            else:
                result["context"] = "Didn't get valid confidence level (1-10). Ask again."
        
        # HIGH CONFIDENCE PATH
        elif self.state == Session4State.HIGH_CONFIDENCE_PATH:
            # Don't ask questions here - just transition
            result["next_state"] = Session4State.HOW_WILL_YOU_REMEMBER_TO_DO_YOUR_GOAL
            result["context"] = "Acknowledge high confidence briefly (1 sentence). Ask: 'How will you remember to work on these goals and keep them going after our program ends?'"

        # LOW CONFIDENCE - WHAT SUCCESSES
        elif self.state == Session4State.LOW_CONFIDENCE_WHAT_SUCCESSES:
            # Check if they just gave us a confidence number (shouldn't happen but handle it)
            confidence_num = extract_number(user_input)
            if confidence_num and 1 <= confidence_num <= 10:
                self.session_data["confidence_level"] = confidence_num
                if confidence_num >= 7:
                    # Actually high confidence - go to high confidence path
                    result["next_state"] = Session4State.HIGH_CONFIDENCE_PATH
                    result["context"] = "High confidence! Transition to tracking."
                    return result
            
            # First time: ask about successes
            if not self._has_asked_question("what_successes"):
                self._mark_question_asked("what_successes")
                result["context"] = "Low confidence. Ask: 'What successes have you had so far, even small ones, that show you can do this?'"
                return result
            
            # Track how many exchanges we've had
            success_discussion_count = self.session_data.get('success_discussion_count', 0)
            self.session_data['success_discussion_count'] = success_discussion_count + 1
            
            # After 1-2 exchanges, transition to making goal more achievable
            if success_discussion_count >= 1:
                result["next_state"] = Session4State.LOW_CONFIDENCE_HOW_CAN_WE_MAKE_IT_MORE_ACHIEVABLE
                result["context"] = "Acknowledged their successes and support. Ask: 'How can we adjust your goal to make it feel more achievable? Would scaling it back help build your confidence?'"
            else:
                # One more brief follow-up about support
                result["context"] = "Briefly acknowledge. Ask one more question about their support system or what's helped them succeed before."
        
        # LOW CONFIDENCE - HOW TO MAKE MORE ACHIEVABLE
        elif self.state == Session4State.LOW_CONFIDENCE_HOW_CAN_WE_MAKE_IT_MORE_ACHIEVABLE:
            # Track how many exchanges
            achievable_discussion_count = self.session_data.get('achievable_discussion_count', 0)
            self.session_data['achievable_discussion_count'] = achievable_discussion_count + 1
    
    #        After 1-2 exchanges, move to tracking
            if achievable_discussion_count >= 1:
                result["next_state"] = Session4State.HOW_WILL_YOU_REMEMBER_TO_DO_YOUR_GOAL
                result["context"] = "Acknowledged adjustments. Ask: 'How will you remember to work on these goals and keep them going after our program ends?'"
            else:
                result["context"] = "Help them think through adjustments. Keep it brief - one more exchange max."
        
        # HOW WILL YOU REMEMBER TO DO YOUR GOAL
        elif self.state == Session4State.HOW_WILL_YOU_REMEMBER_TO_DO_YOUR_GOAL:
            # Check for goodbye/ending indicators
            goodbye_indicators = ["bye", "goodbye", "thank you", "thanks", "see you"]
            has_goodbye = any(word in user_lower for word in goodbye_indicators)

            if not self._has_asked_question("tracking_method"):
                # First time: ask the tracking question
                self._mark_question_asked("tracking_method")
                result["context"] = "Ask: 'How will you remember to work on these goals and keep them going after our program ends?'"
                result["next_state"] = Session4State.ANY_FINAL_QUESTIONS
            elif has_goodbye:
                # They're already saying goodbye - just acknowledge briefly
                result["next_state"] = Session4State.END_SESSION
                self.session_data["final_goodbye_given"] = True
                result["context"] = "Brief goodbye only (e.g., 'Take care, Jade' or 'Goodbye, Jade. Best wishes!'). Maximum 1 sentence."
                result["trigger_rag"] = False 

        # ANY FINAL QUESTIONS
        elif self.state == Session4State.ANY_FINAL_QUESTIONS:
            # Check for goodbye/ending indicators
            goodbye_indicators = ["bye", "goodbye", "thank you", "thanks", "see you"]
            has_goodbye = any(word in user_lower for word in goodbye_indicators)
            
            # Check if we've asked the question yet
            if not self._has_asked_question("final_questions"):
                self._mark_question_asked("final_questions")
                result["context"] = "Ask: 'Do you have any final questions or anything else you'd like to discuss before we end?'"
                return result
            elif check_negative(user_input) or "no" in user_lower:
                # They said no - give final goodbye and END
                result["next_state"] = Session4State.END_SESSION
                self.session_data["final_goodbye_given"] = True
                result["context"] = "Give final farewell for the entire 4-session program. Warm, encouraging, brief (2-3 sentences). This is THE END."
                # Don't set trigger_rag to False here - we want to generate the goodbye message
            elif has_goodbye:
                # They're already saying goodbye - just acknowledge briefly
                result["next_state"] = Session4State.END_SESSION
                self.session_data["final_goodbye_given"] = True
                result["context"] = "Brief goodbye only (e.g., 'Take care, Jade' or 'Goodbye, Jade. Best wishes!'). Maximum 1 sentence."
                result["trigger_rag"] = False 
            else:
                # They have a question - answer it, then ask if there's anything else
                result["context"] = "Answer their question thoughtfully, then ask: 'Is there anything else before we finish?'"

        #END SESSION
        elif self.state == Session4State.END_SESSION:
            # Session is complete - no more responses
            if self.session_data.get("final_goodbye_given"):
                result["context"] = "Session complete. No response needed."
                result["trigger_rag"] = False
                return result
            else:
                # First time entering END_SESSION - give final goodbye
                self.session_data["final_goodbye_given"] = True
                result["context"] = "Give the final farewell. This is the end of all 4 sessions. Warm, brief (2-3 sentences), and truly final."
                result["trigger_rag"] = False
        
        return result
    
    def get_system_prompt_addition(self) -> str:
        """Get state-specific system prompt additions"""
        return get_session4_prompt(
            state_value=self.state.value,
            session_data=self.session_data
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of session data"""
        return {
            "current_state": self.state.value,
            "session_data": self.session_data,
            "duration_turns": self.session_data["turn_count"]
        }
    
    def save_session(self, filename: str = None, conversation_history: list = None):
        """Save session using unified storage format and database"""
        self._log_debug("Saving Session 4 with unified format")
        
        # Build complete goals list
        all_goals = []
        
        # Add previous goals with updated status
        for prev_goal in self.session_data.get("previous_goals", []):
            goal_entry = {
                "goal": prev_goal["goal"],
                "confidence": prev_goal.get("confidence"),
                "stress": self.session_data.get("stress_level"),
                "session_created": prev_goal.get("session_created", 3),
                "created_at": None
            }
            
            # Determine status
            path = self.session_data.get("path_chosen")
            if path == "new":
                goal_entry["status"] = "dropped"
            else:
                goal_entry["status"] = "active"
            
            all_goals.append(goal_entry)
        
        # Add new goals from this session
        for new_goal in self.session_data.get("new_goals", []):
            goal_entry = {
                "goal": new_goal,
                "confidence": self.session_data.get("confidence_level"),
                "stress": self.session_data.get("stress_level"),
                "session_created": 4,
                "status": "active",
                "created_at": self.session_data.get("session_start")
            }
            all_goals.append(goal_entry)
        
        # Preserve discovery info
        discovery = self.session_data.get("discovery_info", {})
        
        # Prepare session metadata
        session_metadata = {
            "turn_count": self.session_data.get("turn_count"),
            "stress_level": self.session_data.get("stress_level"),
            "goals_achieved": self.session_data.get("goals_achieved"),
            "what_happened": self.session_data.get("what_happened"),
            "path_chosen": self.session_data.get("path_chosen"),
            "new_goals": self.session_data.get("new_goals", []),
            "confidence_level": self.session_data.get("confidence_level"),
            "tracking_method": self.session_data.get("tracking_method"),
        }
        
        # Build full data structure
        full_data = {
            "user_profile": {
                "uid": self.uid,
                "name": self.session_data.get("user_name"),
                "goals": all_goals,
                "discovery_questions": discovery
            },
            "session_info": {
                "session_number": 4,
                "current_state": self.state.value,
                "metadata": session_metadata
            },
            "chat_history": conversation_history or []
        }
        
        # Save to database
        if save_session_to_db(self.uid, 4, full_data):
            self._log_debug(f"Session 4 saved to database for UID: {self.uid}")
        else:
            self._log_debug("Warning: Failed to save Session 4 to database")
        
        # Also save to file
        filename = save_unified_session(
            uid=self.uid,
            user_name=self.session_data.get("user_name"),
            session_number=4,
            current_state=self.state.value,
            discovery=discovery,
            goals=all_goals,
            session_metadata=session_metadata,
            conversation_history=conversation_history,
            filename=filename
        )
        
        self._log_debug(f"Session 4 saved to {filename}")
        return filename
    
    def load_session(self, filename: str = None, uid: str = None, inject_history: bool = True):
        """
        Load session data from database or file and optionally inject into conversation history
        
        Args:
            filename: Path to JSON file (optional)
            uid: User ID for database lookup (optional)
            inject_history: If True, return chat history for injection into conversation
        
        Returns:
            List of chat history messages if inject_history=True, else empty list
        """
        from utils.unified_storage import load_unified_session
        
        data = None
        
        # Try database first
        if uid:
            self._log_debug(f"Loading Session 4 from database for UID: {uid}")
            data = load_session_from_db(uid, 4)
            
            if not data:
                self._log_debug("No Session 4 found in database, trying file...")
        
        # Fall back to file
        if not data and filename:
            self._log_debug(f"Loading Session 4 from file: {filename}")
            data = load_unified_session(filename)
        
        if not data:
            self._log_debug("No session data found")
            return []
        
        # Extract and restore data
        profile = data.get("user_profile", {})
        session_info = data.get("session_info", {})
        
        self.state = Session4State(session_info.get("current_state", "greetings"))
        self.uid = profile.get("uid")
        
        self.session_data["uid"] = self.uid
        self.session_data["user_name"] = profile.get("name")
        self.session_data["discovery_info"] = profile.get("discovery_questions", {})
        
        # Restore goals
        all_goals = profile.get("goals", [])
        self.session_data["previous_goals"] = []
        self.session_data["new_goals"] = []
        
        for goal in all_goals:
            if goal.get("session_created") in [1, 2, 3]:
                self.session_data["previous_goals"].append({
                    "goal": goal.get("goal"),
                    "confidence": goal.get("confidence"),
                    "session_created": goal.get("session_created")
                })
            elif goal.get("session_created") == 4:
                self.session_data["new_goals"].append(goal.get("goal"))
        
        # Restore metadata
        metadata = session_info.get("metadata", {})
        self.session_data["turn_count"] = metadata.get("turn_count", 0)
        self.session_data["stress_level"] = metadata.get("stress_level")
        self.session_data["goals_achieved"] = metadata.get("goals_achieved")
        self.session_data["path_chosen"] = metadata.get("path_chosen")
        self.session_data["tracking_method"] = metadata.get("tracking_method")
        
        self._log_debug("Session 4 loaded successfully")
        
        # Return chat history for injection if requested
        if inject_history:
            chat_history = data.get("chat_history", [])
            self._log_debug(f"Returning {len(chat_history)} chat history messages for injection")
            return chat_history
        
        return []