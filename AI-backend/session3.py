from enum import Enum
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
import re

# Utilities
from utils.smart_evaluation import evaluate_smart_goal_with_llm, heuristic_smart_check, create_concise_goal
from utils.unified_storage import save_unified_session, get_active_goals, extract_user_profile
from utils.state_prompts import get_session3_prompt
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

class Session3State(Enum):
    """States for Session 3 conversation flow"""
    GREETINGS = "greetings"
    CHECK_IN_GOALS = "check_in_goals"
    STRESS_LEVEL = "stress_level"
    DISCOVERY_QUESTIONS = "discovery_questions"
    GOAL_COMPLETION = "goal_completion"
    GOALS_FOR_NEXT_WEEK = "goals_for_next_week"
    
    # Path 1: Same goals as last week
    SAME_GOALS_SUCCESSES_CHALLENGES = "same_goals_successes_challenges"
    SAME_ANYTHING_TO_CHANGE = "same_anything_to_change" 
    SAME_WHAT_CONCERNS = "same_what_concerns"  
    SAME_EXPLORE_SOLUTIONS = "same_explore_solutions" 
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


class Session3Manager:
    """Manages conversation flow for Session 3"""
    
    def __init__(self, user_profile: Dict = None, llm_client=None, debug=True):
        self.debug = debug
        self.state = Session3State.GREETINGS
        
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
                "session_created": g.get("session_created", 2)
            } for g in active_goals]
            
            # Get discovery info
            discovery_info = user_profile.get("discovery_questions", {})
        
        # Extract discovery questions (placeholder - can be expanded)
        discovery_questions = []
        
        self.session_data = {
            "uid": self.uid,
            "user_name": user_name,
            "previous_goals": previous_goals,
            "discovery_info": discovery_info,
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
            "goal_parts": [], 
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
            "explored_low_confidence": False,
            "questions_asked": set(),
            "final_goodbye_given": False,
            "check_in_asked": False,
        }
        self.llm_client = llm_client
        self._log_debug(f"Session 3 initialized with user: {user_name}, UID: {self.uid}")
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
    
    def get_state(self) -> Session3State:
        return self.state
    
    def set_state(self, new_state: Session3State):
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
        
        # CRITICAL: If we're in END_SESSION and goodbye was already given, stay there
        if self.state == Session3State.END_SESSION and self.session_data.get("final_goodbye_given"):
            result["context"] = "Session already ended. Politely acknowledge but don't continue conversation."
            result["trigger_rag"] = False
            return result
        
        # GREETINGS STATE
        if self.state == Session3State.GREETINGS:
            if user_input.strip() == "[START_SESSION]":
                result["context"] = f"Welcome {self.session_data.get('user_name', 'them')} back warmly. It's Session 3. Keep it brief."
                return result
            
            result["next_state"] = Session3State.CHECK_IN_GOALS
            result["context"] = "Acknowledge briefly. Move to check-in on their goals."
            self._mark_question_asked("greeting")
        
        # CHECK_IN_GOALS STATE - Simplified
        elif self.state == Session3State.CHECK_IN_GOALS:
            # Mark that we've asked about check-in
            if not self.session_data.get("check_in_asked"):
                self.session_data["check_in_asked"] = True
                result["context"] = "Ask how their goals went this past week. Be warm and interested."
            else:
                # They've responded - move to stress level
                result["next_state"] = Session3State.STRESS_LEVEL
                result["context"] = "Acknowledge their progress. Now ask about stress level on a scale of 1-10."
                self._mark_question_asked("check_in_goals")
        
        # STRESS_LEVEL STATE
        elif self.state == Session3State.STRESS_LEVEL:
            # Try to extract a stress level number (1-10)
            stress = extract_number(user_input)
            
            # Validate it's in range
            if stress and 1 <= stress <= 10:
                self.session_data["stress_level"] = stress
                result["next_state"] = Session3State.GOALS_FOR_NEXT_WEEK
                result["context"] = f"Stress level noted: {stress}/10. Ask what they want to focus on for goals."
                self._mark_question_asked("stress_level")
            else:
                # Didn't get valid stress level
                result["context"] = "Didn't get valid stress number (1-10). Ask: 'On a scale of 1-10, what was your stress level this past week?'"
        
        # GOALS_FOR_NEXT_WEEK STATE
        elif self.state == Session3State.GOALS_FOR_NEXT_WEEK:
            # Detect intent
            same_indicators = ["same", "keep", "continue", "current", "these"]
            different_indicators = ["different", "change", "new", "adjust"]
            
            has_same = any(word in user_lower for word in same_indicators)
            has_different = any(word in user_lower for word in different_indicators)
            
            if has_same and not has_different:
                self.session_data["path_chosen"] = "same"
                self.session_data["goals_to_keep"] = [g["goal"] for g in self.session_data.get("previous_goals", [])]
                result["next_state"] = Session3State.SAME_GOALS_SUCCESSES_CHALLENGES
                result["context"] = "Same goals path. Ask about successes and challenges."
            elif has_different or has_same:  # They want to adjust
                self.session_data["path_chosen"] = "different"
                result["next_state"] = Session3State.DIFFERENT_WHICH_GOALS
                result["context"] = "Different/adjustment path. Ask which goals to keep and what to change."
            else:
                result["context"] = "Clarify: Would you like to keep your current goals or make some changes?"
        
        # PATH 1: SAME GOALS
        elif self.state == Session3State.SAME_GOALS_SUCCESSES_CHALLENGES:
            # Capture successes and challenges
            if "success" in user_lower or "good" in user_lower or "well" in user_lower:
                successes = self.session_data.get("successes", [])
                successes.append(user_input)
                self.session_data["successes"] = successes
            
            if "challenge" in user_lower or "difficult" in user_lower or "hard" in user_lower:
                challenges = self.session_data.get("challenges", [])
                challenges.append(user_input)
                self.session_data["challenges"] = challenges
            
            result["next_state"] = Session3State.SAME_ANYTHING_TO_CHANGE
            result["context"] = "Successes and challenges noted. Ask if anything needs to change."
        
        elif self.state == Session3State.SAME_ANYTHING_TO_CHANGE:
            if check_affirmative(user_input):
                self.session_data["adjustments_discussed"] = True
                result["next_state"] = Session3State.SAME_WHAT_CONCERNS
                result["context"] = "They want changes. Ask what concerns them."
            else:
                result["next_state"] = Session3State.CONFIDENCE_CHECK
                result["context"] = "No changes needed. Move to confidence check."
        
        elif self.state == Session3State.SAME_WHAT_CONCERNS:
            concerns = self.session_data.get("changes_needed", {})
            concerns["concerns"] = user_input
            self.session_data["changes_needed"] = concerns
            result["next_state"] = Session3State.SAME_EXPLORE_SOLUTIONS
            result["context"] = "Concerns noted. Explore solutions together."
        
        elif self.state == Session3State.SAME_EXPLORE_SOLUTIONS:
            solutions = self.session_data.get("solutions", {})
            solutions["discussed"] = user_input
            self.session_data["solutions"] = solutions
            result["next_state"] = Session3State.CONFIDENCE_CHECK
            result["context"] = "Solutions explored. Move to confidence check."
        
        # PATH 2: DIFFERENT GOALS (keeping some + new)
        elif self.state == Session3State.DIFFERENT_WHICH_GOALS:
            # They're describing what they want to keep/change
            # Simple approach: assume they've told us, move to confirmation
            result["next_state"] = Session3State.CONFIDENCE_CHECK
            result["context"] = "They've indicated their goal direction. Move to confidence check."
        
        elif self.state == Session3State.DIFFERENT_KEEPING_AND_NEW:
            if is_likely_goal(user_input):
                self.session_data["current_goal"] = user_input
                result["next_state"] = Session3State.REFINE_GOAL
                result["context"] = "New goal identified. Refine it to be SMART."
            else:
                result["context"] = "Encourage them to share their new goal."
        
        # PATH 3: JUST NEW GOALS
        elif self.state == Session3State.JUST_NEW_GOALS:
            if is_likely_goal(user_input):
                self.session_data["current_goal"] = user_input
                result["next_state"] = Session3State.REFINE_GOAL
                result["context"] = "New goal captured. Move to refinement."
            else:
                result["context"] = "Encourage them to share their new goal."
        
        # REFINE_GOAL STATE
        elif self.state == Session3State.REFINE_GOAL:
            current_goal = self.session_data.get("current_goal")
            
            if current_goal:
                # Evaluate SMART
                smart_result = self.evaluate_smart_goal(current_goal)
                self.session_data["goal_smart_analysis"] = smart_result
                
                if smart_result["is_smart"]:
                    # Goal is SMART, accept it
                    new_goals = self.session_data.get("new_goals", [])
                    new_goals.append(current_goal)
                    self.session_data["new_goals"] = new_goals
                    result["next_state"] = Session3State.CONFIDENCE_CHECK
                    result["context"] = "Goal is SMART. Move to confidence check."
                else:
                    # Need refinement
                    self.session_data["smart_refinement_attempts"] += 1
                    
                    if self.session_data["smart_refinement_attempts"] >= 2:
                        # Accept after 2 attempts
                        new_goals = self.session_data.get("new_goals", [])
                        new_goals.append(current_goal)
                        self.session_data["new_goals"] = new_goals
                        result["next_state"] = Session3State.CONFIDENCE_CHECK
                        result["context"] = "Goal accepted after refinement attempts. Move to confidence."
                    else:
                        missing = ", ".join(smart_result["missing_criteria"])
                        result["context"] = f"Goal needs work. Missing: {missing}. Help refine it."
            else:
                result["context"] = "No current goal. Ask them to state their goal."
        
        # CONFIDENCE_CHECK STATE
        elif self.state == Session3State.CONFIDENCE_CHECK:
            # Try to extract confidence number (1-10)
            confidence = extract_number(user_input)
            
            # Validate it's in range
            if confidence and 1 <= confidence <= 10:
                self.session_data["confidence_level"] = confidence
                
                if confidence < 7:
                    result["next_state"] = Session3State.LOW_CONFIDENCE
                    result["context"] = f"Low confidence ({confidence}/10). Explore what would help."
                else:
                    result["next_state"] = Session3State.HIGH_CONFIDENCE
                    result["context"] = f"Good confidence ({confidence}/10). Move forward."
            else:
                result["context"] = "Didn't get valid confidence number (1-10). Ask: 'On a scale of 1-10, how confident are you about achieving this goal?'"
        
        # LOW_CONFIDENCE STATE
        elif self.state == Session3State.LOW_CONFIDENCE:
            if not self.session_data.get("explored_low_confidence"):
                self.session_data["explored_low_confidence"] = True
                result["next_state"] = Session3State.MAKE_ACHIEVABLE
                result["context"] = "Low confidence explored. Ask how to make it more achievable."
            else:
                result["next_state"] = Session3State.REMEMBER_GOAL
                result["context"] = "Explored enough. Move to tracking method."
        
        # HIGH_CONFIDENCE STATE
        elif self.state == Session3State.HIGH_CONFIDENCE:
            result["next_state"] = Session3State.REMEMBER_GOAL
            result["context"] = "High confidence. Move to tracking method."
        
        # MAKE_ACHIEVABLE STATE
        elif self.state == Session3State.MAKE_ACHIEVABLE:
            # They've discussed making it achievable
            result["next_state"] = Session3State.REMEMBER_GOAL
            result["context"] = "Adjustments discussed. Move to tracking method."
        
        # REMEMBER_GOAL STATE
        elif self.state == Session3State.REMEMBER_GOAL:
            self.session_data["tracking_method_discussed"] = True
            result["next_state"] = Session3State.MORE_GOALS_CHECK
            result["context"] = "Tracking method noted. Ask if they want more goals."
        
        # MORE_GOALS_CHECK STATE
        elif self.state == Session3State.MORE_GOALS_CHECK:
            if check_wants_more(user_input):
                # They want to add another goal
                self.session_data["current_goal"] = None
                self.session_data["smart_refinement_attempts"] = 0
                result["next_state"] = Session3State.JUST_NEW_GOALS
                result["context"] = "They want another goal. Ask them to share it."
            else:
                # Done with goals
                result["next_state"] = Session3State.END_SESSION
                result["context"] = "No more goals. Give final summary and farewell."
        
        # END_SESSION STATE
        elif self.state == Session3State.END_SESSION:
            self.session_data["final_goodbye_given"] = True
            result["context"] = "Session ended. Polite acknowledgment only."
            result["trigger_rag"] = False
        
        if result["next_state"]:
            self._log_debug(f"Next state will be: {result['next_state'].value}")
        
        return result
    
    def get_system_prompt_addition(self) -> str:
        """Get state-specific system prompt additions"""
        return get_session3_prompt(
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
        self._log_debug("Saving Session 3 with unified format")
        
        # Build complete goals list
        all_goals = []
        
        # Add previous goals with updated status
        for prev_goal in self.session_data.get("previous_goals", []):
            goal_entry = {
                "goal": prev_goal["goal"],
                "confidence": prev_goal.get("confidence"),
                "stress": self.session_data.get("stress_level"),
                "session_created": prev_goal.get("session_created", 2),
                "created_at": None  # From previous session
            }
            
            # Determine status based on path chosen
            path = self.session_data.get("path_chosen")
            goals_to_keep = self.session_data.get("goals_to_keep", [])
            
            if path == "new":
                goal_entry["status"] = "dropped"
            elif path == "same":
                goal_entry["status"] = "active"
            elif path == "different":
                if prev_goal["goal"] in goals_to_keep:
                    goal_entry["status"] = "active"
                else:
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
                "session_created": 3,
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
            "path_chosen": self.session_data.get("path_chosen"),
            "goals_to_keep": self.session_data.get("goals_to_keep", []),
            "new_goals": self.session_data.get("new_goals", []),
            "challenges": self.session_data.get("challenges", []),
            "successes": self.session_data.get("successes", []),
            "discovery_responses": self.session_data.get("discovery_responses", []),
            "tracking_method_discussed": self.session_data.get("tracking_method_discussed", False),
            "confidence_level": self.session_data.get("confidence_level"),
            "current_goal": self.session_data.get("current_goal")
        }
        
        # Build full data structure for database
        full_data = {
            "user_profile": {
                "uid": self.uid,
                "name": self.session_data.get("user_name"),
                "goals": all_goals,
                "discovery_questions": discovery
            },
            "session_info": {
                "session_number": 3,
                "current_state": self.state.value,
                "metadata": session_metadata
            },
            "chat_history": conversation_history or []
        }
        
        # Save to PostgreSQL database
        if save_session_to_db(self.uid, 3, full_data):
            self._log_debug(f"Session 3 saved to database for UID: {self.uid}")
        else:
            self._log_debug("Warning: Failed to save Session 3 to database")
        
        # Also save to file (backup/legacy support)
        filename = save_unified_session(
            uid=self.uid,
            user_name=self.session_data.get("user_name"),
            session_number=3,
            current_state=self.state.value,
            discovery=discovery,
            goals=all_goals,
            session_metadata=session_metadata,
            conversation_history=conversation_history,
            filename=filename
        )
        
        self._log_debug(f"Session 3 saved to {filename}")
        return filename

    def load_session(self, filename: str = None, uid: str = None):
        """Load session data from database or file"""
        from utils.unified_storage import load_unified_session
        
        data = None
        
        # Try loading from database first
        if uid:
            self._log_debug(f"Loading Session 3 from database for UID: {uid}")
            data = load_session_from_db(uid, 3)
            
            if not data:
                self._log_debug("No Session 3 found in database, trying file...")
        
        # Fall back to file if database load failed or no uid provided
        if not data and filename:
            self._log_debug(f"Loading Session 3 from file: {filename}")
            data = load_unified_session(filename)
        
        if not data:
            self._log_debug("No session data found")
            return []
        
        # Extract user profile
        profile = data.get("user_profile", {})
        session_info = data.get("session_info", {})
        
        # Restore state
        self.state = Session3State(session_info.get("current_state", "greetings"))
        self.uid = profile.get("uid")
        
        # Restore session data
        self.session_data["uid"] = self.uid
        self.session_data["user_name"] = profile.get("name")
        
        # Restore discovery info
        self.session_data["discovery_info"] = profile.get("discovery_questions", {})
        
        # Restore goals
        all_goals = profile.get("goals", [])
        
        # Separate previous goals and new goals from Session 3
        self.session_data["previous_goals"] = []
        self.session_data["new_goals"] = []
        
        for goal in all_goals:
            if goal.get("session_created") in [1, 2]:
                self.session_data["previous_goals"].append({
                    "goal": goal.get("goal"),
                    "confidence": goal.get("confidence"),
                    "session_created": goal.get("session_created")
                })
            elif goal.get("session_created") == 3:
                self.session_data["new_goals"].append(goal.get("goal"))
        
        # Restore metadata
        metadata = session_info.get("metadata", {})
        self.session_data["turn_count"] = metadata.get("turn_count", 0)
        self.session_data["stress_level"] = metadata.get("stress_level")
        self.session_data["path_chosen"] = metadata.get("path_chosen")
        self.session_data["goals_to_keep"] = metadata.get("goals_to_keep", [])
        self.session_data["challenges"] = metadata.get("challenges", [])
        self.session_data["successes"] = metadata.get("successes", [])
        
        self._log_debug(f"Session 3 loaded successfully")
        
        return data.get("chat_history", [])