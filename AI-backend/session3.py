from enum import Enum
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
import re

# Utilities
from utils.smart_evaluation import evaluate_smart_goal_with_llm, heuristic_smart_check, create_concise_goal
from utils.session_storage import save_session_data, load_session_data
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

class Session3State(Enum):
    """States for Session 2 conversation flow"""
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
    """Manages conversation flow for Session 2"""
    
    def __init__(self, session2_data: Dict = None, llm_client=None, debug=True):
        self.debug = debug
        self.state = Session3State.GREETINGS
        
        user_name = session2_data.get("user_name") if session2_data else None
        if user_name:
            user_name = user_name.title()
        
        discovery_questions = []
        if session2_data and session2_data.get("goal_details"):
            for goal_info in session2_data["goal_details"]:
                if goal_info.get("discovery_questions"):
                    discovery_questions.extend(goal_info["discovery_questions"])
        
        self.session_data = {
            "user_name": user_name,
            "previous_goals": session2_data.get("goal_details", []) if session2_data else [],
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
            "final_goodbye_given": False  # NEW: Track if goodbye was given
        }
        self.llm_client = llm_client
        self._log_debug(f"Session initialized with user: {user_name}")
        self._log_debug(f"Discovery questions loaded: {len(discovery_questions)}")
    
    def _create_concise_goal(self, full_goal: str) -> str:
        """Create a concise version of the goal for storage - NOW USES UTILITY"""
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
    
    def _heuristic_smart_check(self, goal: str) -> Dict[str, Any]:
        """Simple heuristic-based SMART check as fallback - NOW USES UTILITY"""
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
        
        if self.state == Session3State.GREETINGS:
            if user_input.strip() == "[START_SESSION]":
                result["context"] = f"Welcome {self.session_data.get('user_name', 'them')} back warmly. It's Session 3. Keep it brief."
                return result
            
            result["next_state"] = Session3State.CHECK_IN_GOALS
            result["context"] = "Acknowledge briefly. Move to check-in."
            self._mark_question_asked("greeting")
        
        elif self.state == Session3State.CHECK_IN_GOALS:
            result["next_state"] = Session3State.STRESS_LEVEL
            result["context"] = "Acknowledge briefly. Ask stress level (1-10 scale)."
            self._mark_question_asked("check_in")
        
        elif self.state == Session3State.STRESS_LEVEL:
            stress = extract_number(user_input)
            if stress:
                self.session_data["stress_level"] = stress
                self._mark_question_asked("stress_level")
                
                if self.session_data.get("discovery_questions"):
                    result["next_state"] = Session3State.DISCOVERY_QUESTIONS
                    result["context"] = f"Note stress: {stress}/10. Ask ONE discovery question."
                else:
                    result["next_state"] = Session3State.GOAL_COMPLETION
                    result["context"] = f"Note stress: {stress}/10. Ask about goal completion."
            else:
                result["context"] = "Ask for stress level as a number (1-10)."
        
        elif self.state == Session3State.DISCOVERY_QUESTIONS:
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
                result["next_state"] = Session3State.GOAL_COMPLETION
                result["context"] = "Acknowledge. Ask about goal completion."
        
        elif self.state == Session3State.GOAL_COMPLETION:
            self._mark_question_asked("goal_completion")
            result["next_state"] = Session3State.GOALS_FOR_NEXT_WEEK
            result["context"] = "Acknowledge their progress. Ask about next week's goals (same, keep some + add new, or completely new)."
        
        elif self.state == Session3State.GOALS_FOR_NEXT_WEEK:
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
                result["next_state"] = Session3State.DIFFERENT_KEEPING_AND_NEW
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
                    result["next_state"] = Session3State.DIFFERENT_KEEPING_AND_NEW
                    result["context"] = "They want to keep current goals and add new. Ask what new goal."
                # "Same goal only" = same path
                elif has_same and not has_add and not has_different:
                    self.session_data["path_chosen"] = "same"
                    if self.session_data.get("previous_goals"):
                        self.session_data["goals_to_keep"] = [g['goal'] for g in self.session_data["previous_goals"]]
                    result["next_state"] = Session3State.SAME_GOALS_SUCCESSES_CHALLENGES
                    result["context"] = "Keeping same goal. Ask what went well and what was challenging."
                # "Completely new" = new path
                elif has_different and not has_same:
                    self.session_data["path_chosen"] = "new"
                    result["next_state"] = Session3State.JUST_NEW_GOALS
                    result["context"] = "New goals. Ask what they'd like to focus on."
                else:
                    result["context"] = "Clarify: same goal, keep some + add new, or completely new?"
            else:
                result["context"] = "Path already chosen. Continue."
        
        elif self.state == Session3State.SAME_GOALS_SUCCESSES_CHALLENGES:
            if self._has_asked_question("successes_challenges"):
                # They responded to successes/challenges - now ask if anything needs changing
                result["next_state"] = Session3State.SAME_ANYTHING_TO_CHANGE
                result["context"] = "Acknowledge their response briefly (1 sentence). Ask: 'Is there anything about this goal that needs to be changed or worked on?'"
            else:
                # First time - ask the question
                self._mark_question_asked("successes_challenges")
                result["context"] = "Ask: What went well? What was challenging?"
        
        elif self.state == Session3State.SAME_ANYTHING_TO_CHANGE:
            wants_change = any(w in user_lower for w in ["yes", "yeah", "change", "modify", "adjust", "different", "worry", "concerned", "fear", "harder"])
            no_change = any(w in user_lower for w in ["no", "nope", "good", "fine", "keep", "same"])
            
            if wants_change:
                result["next_state"] = Session3
                result["next_state"] = Session3State.END_SESSION
                result["context"] = "They're happy with the goal as-is. Give final goodbye."
                self.session_data["final_goodbye_given"] = True
            else:
                result["context"] = "Clarify: Do they want to change anything about their goal? Yes or no?"
        
        elif self.state == Session3State.SAME_WHAT_CONCERNS:
            # They're expressing concerns or proposing solutions
            result["next_state"] = Session3State.SAME_EXPLORE_SOLUTIONS
            result["context"] = "Acknowledge their concerns. Ask what solutions or adjustments they're thinking about."
        
        elif self.state == Session3State.SAME_EXPLORE_SOLUTIONS:
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
                    result["next_state"] = Session3State.CONFIDENCE_CHECK
                    result["context"] = "Modified goal is SMART! Ask confidence (1-10)."
                else:
                    result["next_state"] = Session3State.REFINE_GOAL
                    result["context"] = f"Modified goal missing: {', '.join(smart_eval['missing_criteria'])}. Help refine it."
            else:
                # Still exploring - help them think through solutions
                result["context"] = "Guide them toward a specific adjustment. What would make it more achievable?"
        
        elif self.state == Session3State.SAME_NOT_SUCCESSFUL:
            result["next_state"] = Session3State.END_SESSION
            result["context"] = "Acknowledge challenges. Encourage. Give final goodbye."
            self.session_data["final_goodbye_given"] = True
        
        elif self.state == Session3State.SAME_SUCCESSFUL:
            result["next_state"] = Session3State.END_SESSION
            result["context"] = "Celebrate success. Give final goodbye."
            self.session_data["final_goodbye_given"] = True
        
        elif self.state == Session3State.DIFFERENT_WHICH_GOALS:
            # Check if we already identified which goals to keep
            if self.session_data.get("goals_to_keep_identified"):
                # Already know which goals - this is them describing the new goal
                result["next_state"] = Session3State.DIFFERENT_KEEPING_AND_NEW
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
                result["next_state"] = Session3State.DIFFERENT_KEEPING_AND_NEW
                result["context"] = f"Noted keeping: {', '.join(goals_mentioned)}. Now ask what new goal they want to add."
            else:
                result["context"] = "Ask which specific previous goals they want to keep."
        
        elif self.state == Session3State.DIFFERENT_KEEPING_AND_NEW:
            goal_candidate = user_input.strip()
            
            # Check if this is a substantial goal description (not just "yes" or single words)
            if is_likely_goal(goal_candidate):
                self.session_data["current_goal"] = goal_candidate
                
                # Only add to new_goals list if it's not already there
                if not self.session_data["new_goals"] or self.session_data["new_goals"][-1] != goal_candidate:
                    self.session_data["new_goals"].append(goal_candidate)
                
                smart_eval = self.evaluate_smart_goal(goal_candidate)
                self.session_data["goal_smart_analysis"] = smart_eval
                self.session_data["smart_refinement_attempts"] = 0
                
                if smart_eval["is_smart"]:
                    result["next_state"] = Session3State.CONFIDENCE_CHECK
                    result["context"] = "Goal is SMART! Ask confidence (1-10)."
                else:
                    result["next_state"] = Session3State.REFINE_GOAL
                    result["context"] = f"Goal needs refinement. Missing: {', '.join(smart_eval['missing_criteria'])}. Guide them to make it more specific."
            else:
                # Still exploring what the new goal should be - don't add anything to goals list yet
                result["context"] = "Ask what new goal they'd like to add. Get more detail about what they want to focus on."
        
        elif self.state == Session3State.JUST_NEW_GOALS:
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
                    result["next_state"] = Session3State.CONFIDENCE_CHECK
                    result["context"] = "Goal is SMART! Ask confidence (1-10)."
                else:
                    result["next_state"] = Session3State.REFINE_GOAL
                    result["context"] = f"Missing: {', '.join(smart_eval['missing_criteria'])}. Guide refinement."
            else:
                # Not a goal yet, keep asking
                result["context"] = "Ask what goal they'd like to focus on."
        
        elif self.state == Session3State.REFINE_GOAL:
            goal_candidate = user_input.strip()
            
            # Check if this is a substantial goal statement (not just "yes" or very short responses)
            is_affirmation = user_lower in ["yes", "yeah", "yep", "no", "nope", "ok", "okay", "correct", "right"]
            is_conversational = any(phrase in user_lower for phrase in [
                "like i said", "i told you", "as i mentioned", "i already said",
                "its going to be fun", "it's fun", "i want to do this", "i will want to",
                "that makes sense", "i understand", "i like", "because"
            ])
            is_confidence_response = re.search(r'\b([1-9]|10)\b', user_input) and "confident" in self.session_data.get("last_coach_response", "").lower()
            
            # If they're giving a confidence number, capture it and transition
            if is_confidence_response:
                numbers = re.findall(r'\d+', user_input)
                if numbers:
                    confidence = int(numbers[0])
                    self.session_data["confidence_level"] = confidence
                    
                    # Complete the goal with what we have
                    complete_goal = " ".join(self.session_data["goal_parts"])
                    concise_goal = self._create_concise_goal(complete_goal)
                    self.session_data["current_goal"] = concise_goal
                    
                    if self.session_data["new_goals"]:
                        self.session_data["new_goals"][-1] = concise_goal
                    else:
                        self.session_data["new_goals"].append(concise_goal)
                    
                    self.session_data["goal_parts"] = []
                    
                    result["next_state"] = Session3State.CONFIDENCE_CHECK
                    result["context"] = f"Confidence captured as {confidence}. Transition to handle confidence level."
                    return result
            
            # If it's a substantive response (not affirmation/conversational), add to goal parts
            if not is_affirmation and not is_conversational and len(goal_candidate.split()) >= 2:
                # Add this piece to the goal parts
                if goal_candidate not in self.session_data["goal_parts"]:
                    self.session_data["goal_parts"].append(goal_candidate)
                
                # Build the complete goal from all parts
                complete_goal = " ".join(self.session_data["goal_parts"])
                
                # Evaluate the complete goal
                smart_eval = self.evaluate_smart_goal(complete_goal)
                self.session_data["goal_smart_analysis"] = smart_eval
                self.session_data["smart_refinement_attempts"] += 1
                
                # If SMART, create a concise version and save it
                if smart_eval["is_smart"]:
                    # Create concise version of goal
                    concise_goal = self._create_concise_goal(complete_goal)
                    self.session_data["current_goal"] = concise_goal
                    
                    if self.session_data["new_goals"]:
                        self.session_data["new_goals"][-1] = concise_goal
                    else:
                        self.session_data["new_goals"].append(concise_goal)
                    
                    # Clear goal parts for next goal
                    self.session_data["goal_parts"] = []
                    
                    result["next_state"] = Session3State.CONFIDENCE_CHECK
                    result["context"] = "Goal is SMART! Ask confidence (1-10)."
                elif self.session_data["smart_refinement_attempts"] >= 4:
                    # After 4 attempts, accept what we have
                    concise_goal = self._create_concise_goal(complete_goal)
                    self.session_data["current_goal"] = concise_goal
                    
                    if self.session_data["new_goals"]:
                        self.session_data["new_goals"][-1] = concise_goal
                    else:
                        self.session_data["new_goals"].append(concise_goal)
                    
                    self.session_data["goal_parts"] = []
                    
                    result["next_state"] = Session3State.CONFIDENCE_CHECK
                    result["context"] = "Move to confidence check after 4 attempts."
                else:
                    # Still needs more work
                    self.session_data["current_goal"] = complete_goal
                    result["context"] = f"Building goal: '{complete_goal}'. Still missing: {', '.join(smart_eval['missing_criteria'])}. Ask specific questions to get those details. DO NOT ask about confidence yet."
            elif is_affirmation:
                # They're confirming - check if current goal is good enough
                if self.session_data.get("goal_parts"):
                    complete_goal = " ".join(self.session_data["goal_parts"])
                    smart_eval = self.evaluate_smart_goal(complete_goal)
                    
                    if smart_eval["is_smart"] or self.session_data["smart_refinement_attempts"] >= 3:
                        # Good enough, move on
                        concise_goal = self._create_concise_goal(complete_goal)
                        self.session_data["current_goal"] = concise_goal
                        
                        if self.session_data["new_goals"]:
                            self.session_data["new_goals"][-1] = concise_goal
                        else:
                            self.session_data["new_goals"].append(concise_goal)
                        
                        self.session_data["goal_parts"] = []
                        
                        result["next_state"] = Session3State.CONFIDENCE_CHECK
                        result["context"] = "Goal confirmed. Ask confidence (1-10)."
                    else:
                        result["context"] = f"Still missing: {', '.join(smart_eval['missing_criteria'])}. Ask for those details."
                else:
                    result["context"] = "Ask them to describe their goal."
            else:
                # Conversational response - don't add to goal, keep asking for goal details
                result["context"] = "That was conversational. Continue refining. Ask specific questions to make the goal SMART (numbers, frequency, timeframe). DO NOT ask about confidence."
        
        elif self.state == Session3State.CONFIDENCE_CHECK:
            # Check if we already have confidence stored
            if self.session_data.get("confidence_level") is not None:
                # Already have confidence - this is a follow-up response
                confidence = self.session_data["confidence_level"]
                
                if confidence <= 7:
                    # Low confidence path
                    if not self.session_data.get("explored_low_confidence"):
                        self.session_data["explored_low_confidence"] = True
                        result["next_state"] = Session3State.LOW_CONFIDENCE
                        result["context"] = "Explore what would help increase confidence."
                    else:
                        # Already explored, move on
                        result["next_state"] = Session3State.MAKE_ACHIEVABLE
                        result["context"] = "Help make goal more achievable."
                else:
                    # High confidence (8-10) - move to tracking
                    is_same = self.session_data.get("path_chosen") == "same"
                    if is_same:
                        result["next_state"] = Session3State.END_SESSION
                        result["context"] = "High confidence on same goal! Give final goodbye."
                        self.session_data["final_goodbye_given"] = True
                    else:
                        result["next_state"] = Session3State.REMEMBER_GOAL
                        result["context"] = "High confidence! Ask about tracking method."
            else:
                # Don't have confidence yet - look for the number
                numbers = re.findall(r'\d+', user_input)
                if numbers:
                    confidence = int(numbers[0])
                    self.session_data["confidence_level"] = confidence
                    
                    # Immediately transition based on confidence
                    if confidence <= 7:
                        result["next_state"] = Session3State.LOW_CONFIDENCE
                        result["context"] = "Low confidence. Explore what would help increase it."
                    else:
                        # High confidence (8-10)
                        is_same = self.session_data.get("path_chosen") == "same"
                        if is_same:
                            result["next_state"] = Session3State.END_SESSION
                            result["context"] = "High confidence on same goal! Give final goodbye."
                            self.session_data["final_goodbye_given"] = True
                        else:
                            result["next_state"] = Session3State.REMEMBER_GOAL
                            result["context"] = "High confidence! Acknowledge briefly, then ask about tracking method."
                else:
                    result["context"] = "Ask for confidence as a number (1-10). Be clear and direct."
        
        elif self.state == Session3State.LOW_CONFIDENCE:
            result["next_state"] = Session3State.MAKE_ACHIEVABLE
            result["context"] = "Explore what would make it achievable."
        
        elif self.state == Session3State.HIGH_CONFIDENCE:
            result["next_state"] = Session3State.REMEMBER_GOAL
            result["context"] = "Ask about tracking."
        
        elif self.state == Session3State.MAKE_ACHIEVABLE:
            is_same = self.session_data.get("path_chosen") == "same"
            if is_same:
                result["next_state"] = Session3State.END_SESSION
                result["context"] = "Acknowledge adjustments. Give final goodbye."
                self.session_data["final_goodbye_given"] = True
            else:
                result["next_state"] = Session3State.REMEMBER_GOAL
                result["context"] = "Ask about tracking."
        
        elif self.state == Session3State.REMEMBER_GOAL:
            result["next_state"] = Session3State.MORE_GOALS_CHECK
            result["context"] = "Acknowledge tracking. Ask if they want another goal."
        
        elif self.state == Session3State.MORE_GOALS_CHECK:
            wants_more = check_wants_more(user_input)
            done = check_done(user_input)
            
            if wants_more:
                self.session_data["current_goal"] = None
                self.session_data["smart_refinement_attempts"] = 0
                result["next_state"] = Session3State.JUST_NEW_GOALS
                result["context"] = "Ask what other goal."
            else:
                result["next_state"] = Session3State.END_SESSION
                result["context"] = "Give final goodbye for Session 2."
                self.session_data["final_goodbye_given"] = True
        
        elif self.state == Session3State.END_SESSION:
            # Already in END_SESSION, just acknowledge politely
            result["context"] = "Session already complete. Politely acknowledge but don't extend conversation."
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
        """Save session data to JSON file"""
        result = save_session_data(
            state_value=self.state.value,
            session_data=self.session_data,
            conversation_history=conversation_history,
            filename=filename,
            session_prefix="session3"
        )
        self._log_debug(f"Session saved to {result}")
        return result
    
    def load_session(self, filename: str):
        """Load session data from JSON file"""
        data = load_session_data(filename)
        
        self.state = Session3State(data["state"])
        self.session_data = data["session_data"]
        
        self._log_debug(f"Session loaded from {filename}")
        
        return data.get("conversation_history", [])