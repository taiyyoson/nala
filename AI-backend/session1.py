from enum import Enum
from typing import Dict, Any, Optional, Tuple
import json
import os
from datetime import datetime
import re

from utils.database import save_session_to_db
from utils.smart_evaluation import evaluate_smart_goal_with_llm, heuristic_smart_check
from utils.unified_storage import save_unified_session, convert_session1_to_unified
from utils.state_prompts import get_session1_prompt
from utils.program_loader import load_program_info
from utils.name_extraction import extract_name_from_text
from utils.state_helpers import (
    create_state_result, 
    check_affirmative, 
    check_negative, 
    extract_number
)
from utils.goal_detection import is_likely_goal
from utils.goal_parser import (
    is_goal_statement,
    extract_goal_from_text,
    enhance_goal_with_details,
    store_goal,
    format_goals_summary,
    extract_refined_goal_from_coach_response,
    check_coach_goal_acceptance
)

class SessionState(Enum):
    """States for Session 1 conversation flow"""
    GREETINGS = "greetings"
    PROGRAM_DETAILS = "program_details"
    QUESTIONS_ABOUT_PROGRAM = "questions_about_program"
    AWAITING_YES_NO = "awaiting_yes_no"
    ANSWERING_QUESTION = "answering_question"
    PROMPT_TALK_ABOUT_SELF = "prompt_talk_about_self"
    GETTING_TO_KNOW_YOU = "getting_to_know_you"
    GOALS = "goals"
    CHECK_SMART = "check_smart"
    REFINE_GOAL = "refine_goal"
    CONFIDENCE_CHECK = "confidence_check"
    LOW_CONFIDENCE = "low_confidence"
    HIGH_CONFIDENCE = "high_confidence"
    ASK_MORE_GOALS = "ask_more_goals"
    REMEMBER_GOAL = "remember_goal"
    END_SESSION = "end_session"


class Session1Manager:
    """Manages conversation flow for Session 1"""
    
    def __init__(self, program_info_file: str = "program_info.txt", llm_client=None, uid: str = None, debug=True):
        self.debug = debug
        self.state = SessionState.GREETINGS
        
        # Generate or use provided UID
        self.uid = uid or f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.session_data = {
            "uid": self.uid,
            "user_name": None,
            "program_questions_asked": [],
            "goals": [],
            "goal_details": [],
            "current_goal": None,
            "goal_smart_analysis": None,
            "smart_refinement_attempts": 0,
            "confidence_level": None,
            "session_start": datetime.now().isoformat(),
            "turn_count": 0,
            "last_coach_response": None,
            "tracking_method_discussed": False,
            "discovery": {
                "free_time_activities": None,
                "general_about": None,
                "current_exercise": None,
                "current_sleep": None,
                "current_eating": None,
                "questions_asked": []
            }
        }
        self.program_info_file = program_info_file
        self.program_info = load_program_info(program_info_file)
        self.llm_client = llm_client
        self._log_debug(f"Session 1 initialized with UID: {self.uid}")
        
    def _log_debug(self, message: str):
        if self.debug:
            print(f"[DEBUG] {message}", flush=True)
    
    def set_llm_client(self, llm_client):
        """Set the LLM client for SMART goal evaluation"""
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
        """Simple heuristic-based SMART check as fallback"""
        return heuristic_smart_check(goal)
    
    def get_state(self) -> SessionState:
        return self.state
    
    def set_state(self, new_state: SessionState):
        old_state = self.state
        self.state = new_state
        self._log_debug(f"STATE TRANSITION: {old_state.value} -> {new_state.value}")
    
    def get_system_prompt_addition(self) -> str:
        """Get state-specific system prompt additions"""
        return get_session1_prompt(
            state_value=self.state.value,
            session_data=self.session_data,
            program_info=self.program_info
        )
    
    def process_user_input(self, user_input: str, last_coach_response: str = None, conversation_history: list = None) -> Dict[str, Any]:
        """
        Process user input and determine state transitions
        
        Args:
            user_input: The user's message
            last_coach_response: The coach's previous response (for detecting coach satisfaction)
            conversation_history: Full conversation history (optional, for checking if topics were discussed)
        
        Returns:
            Dict with next_state, context, and trigger_rag
        """
        user_lower = user_input.lower().strip()
        self.session_data["turn_count"] += 1
        
        self._log_debug(f"Processing input in state: {self.state.value}")
        self._log_debug(f"User input: {user_input[:100]}...")
        
        if last_coach_response:
            self.session_data["last_coach_response"] = last_coach_response
        
        result = create_state_result()
        
        # State machine logic
        if self.state == SessionState.GREETINGS:
            if user_input.strip() == "[START_SESSION]":
                result["next_state"] = None
                result["context"] = "First message. Introduce yourself as Nala and ask for their name."
                return result
            
           # Extract name
            name = extract_name_from_text(user_input)
            if name:
                self.session_data["user_name"] = name

            result["next_state"] = SessionState.PROGRAM_DETAILS
            result["context"] = f"User's name: {self.session_data.get('user_name', 'Not provided')}\n\nExplain program details."
        
        elif self.state == SessionState.PROGRAM_DETAILS:
            if any(word in user_lower for word in ["yes", "yeah", "yep", "sure", "i do", "i have"]):
                result["next_state"] = SessionState.ANSWERING_QUESTION
                result["trigger_rag"] = False
                result["context"] = f"Program Info:\n{self.program_info}\n\nAnswer their question."
                self.session_data["program_questions_asked"].append(user_input)
            elif any(word in user_lower for word in ["no", "nope", "nah", "don't", "dont", "no questions"]):
                result["next_state"] = SessionState.PROMPT_TALK_ABOUT_SELF
                result["context"] = "No questions. Transition to discovery."
            else:
                result["next_state"] = SessionState.AWAITING_YES_NO
                result["context"] = "Ask if they have questions about the program."
        
        elif self.state == SessionState.QUESTIONS_ABOUT_PROGRAM:
            is_asking = '?' in user_input or len(user_input.split()) > 3
            no_more = any(word in user_lower for word in ["no", "nope", "ready", "let's start", "im good", "i'm good", "that's all", "thats all", "no questions", "none"])
            
            if no_more:
                result["next_state"] = SessionState.PROMPT_TALK_ABOUT_SELF
                result["context"] = "User has no more questions. Transition to discovery phase."
            elif is_asking:
                result["next_state"] = SessionState.ANSWERING_QUESTION
                result["trigger_rag"] = False
                result["context"] = f"Program Info:\n{self.program_info}\n\nAnswer their question about the program."
                self.session_data["program_questions_asked"].append(user_input)
            else:
                result["context"] = "Ask if they have any questions about the program."
        
        elif self.state == SessionState.AWAITING_YES_NO:
            coach_asking_about_questions = False
            if self.session_data.get("last_coach_response"):
                coach_lower = self.session_data["last_coach_response"].lower()
                question_prompts = [
                    'do you have any questions',
                    'any questions',
                    'does that help clarify',
                    'does that answer your question',
                    'anything else you',
                    'is there anything'
                ]
                coach_asking_about_questions = any(prompt in coach_lower for prompt in question_prompts)
            
            if check_affirmative(user_input):
                if coach_asking_about_questions and any(word in self.session_data.get("last_coach_response", "").lower() for word in ["does that help", "clarify", "answer your question"]):
                    result["next_state"] = SessionState.PROMPT_TALK_ABOUT_SELF
                    result["context"] = "User's question was answered. Transition to discovery phase."
                elif len(user_input.split()) > 1 or '?' in user_input:
                    result["next_state"] = SessionState.ANSWERING_QUESTION
                    result["trigger_rag"] = False
                    result["context"] = f"Program Info:\n{self.program_info}\n\nAnswer their question."
                    self.session_data["program_questions_asked"].append(user_input)
                else:
                    result["next_state"] = SessionState.QUESTIONS_ABOUT_PROGRAM
                    result["trigger_rag"] = False
                    result["context"] = "User has questions. Ask what they'd like to know."
                    
            if check_negative(user_input):
                result["next_state"] = SessionState.PROMPT_TALK_ABOUT_SELF
                result["context"] = "User has no questions. Transition to discovery phase."
            else:
                if '?' in user_input or len(user_input.split()) <= 3:
                    result["next_state"] = SessionState.ANSWERING_QUESTION
                    result["trigger_rag"] = False
                    result["context"] = f"Program Info:\n{self.program_info}\n\nAnswer their question about: {user_input}"
                    self.session_data["program_questions_asked"].append(user_input)
                else:
                    result["context"] = "Ask user to clarify: do they have questions about the program? (yes/no)"
        
        elif self.state == SessionState.ANSWERING_QUESTION:
            has_more = any(word in user_lower for word in ["yes", "yeah", "another", "one more", "what about", "how about"])
            no_more = any(word in user_lower for word in ["no", "nope", "ready", "let's start", "im good", "i'm good", "that's all", "thats all"])
            
            if has_more:
                result["next_state"] = SessionState.QUESTIONS_ABOUT_PROGRAM
                result["trigger_rag"] = False
                result["context"] = f"Program Info:\n{self.program_info}\n\nUser has another question. Ask what they'd like to know."
            elif no_more:
                result["next_state"] = SessionState.PROMPT_TALK_ABOUT_SELF
                result["context"] = "User ready to start. Transition to discovery phase."
            else:
                result["next_state"] = SessionState.AWAITING_YES_NO
                result["context"] = "Ask if they have any other questions about the program before starting."
        
        elif self.state == SessionState.PROMPT_TALK_ABOUT_SELF:
            result["next_state"] = SessionState.GETTING_TO_KNOW_YOU
            result["context"] = "Transition to discovery. Explain you'll ask questions to know them."
        
        elif self.state == SessionState.GETTING_TO_KNOW_YOU:
            discovery = self.session_data["discovery"]
            asked = discovery["questions_asked"]
            
            user_response = user_input.strip()
            
            # Use utility to check for goal statement
            goal_text = extract_goal_from_text(user_input)
            min_discovery_complete = len(asked) >= 3
            
            if goal_text and min_discovery_complete:
                result["next_state"] = SessionState.GOALS
                result["context"] = f"""User stated a goal after discovery!
Discovery info:
- About: {discovery.get('general_about', 'Not shared')}
- Exercise: {discovery.get('current_exercise', 'Not shared')}
- Sleep: {discovery.get('current_sleep', 'Not shared')}
- Eating: {discovery.get('current_eating', 'Not shared')}
- Free time: {discovery.get('free_time_activities', 'Not shared')}

User's goal statement: "{user_input}"

IMPORTANT: Acknowledge their goal and help them make it SMART."""
                return result
            
            current_question_index = len(asked)
            
            if current_question_index == 0:
                discovery["questions_asked"].append("intro")
            elif current_question_index == 1:
                discovery["general_about"] = user_response
                discovery["questions_asked"].append("general_about")
            elif current_question_index == 2:
                discovery["current_exercise"] = user_response
                discovery["questions_asked"].append("current_exercise")
            elif current_question_index == 3:
                discovery["current_sleep"] = user_response
                discovery["questions_asked"].append("current_sleep")
            elif current_question_index == 4:
                discovery["current_eating"] = user_response
                discovery["questions_asked"].append("current_eating")
            elif current_question_index == 5:
                discovery["free_time_activities"] = user_response
                discovery["questions_asked"].append("free_time")
            
            next_questions = []
            if "general_about" not in asked:
                next_questions.append("general_about")
            if "current_exercise" not in asked:
                next_questions.append("current_exercise")
            if "current_sleep" not in asked:
                next_questions.append("current_sleep")
            if "current_eating" not in asked:
                next_questions.append("current_eating")
            if "free_time" not in asked:
                next_questions.append("free_time")
            
            if not next_questions:
                result["next_state"] = SessionState.GOALS
                result["context"] = f"""Discovery complete!
Info gathered:
- About: {discovery.get('general_about', 'Not shared')}
- Exercise: {discovery.get('current_exercise', 'Not shared')}
- Sleep: {discovery.get('current_sleep', 'Not shared')}
- Eating: {discovery.get('current_eating', 'Not shared')}
- Free time: {discovery.get('free_time_activities', 'Not shared')}

Now transition to goal setting. Ask: "What specific health or wellness goal would you like to focus on?" """
            else:
                next_topic = next_questions[0]
                
                question_prompts = {
                    "general_about": "Ask: 'Tell me a bit about yourself - what's important to you right now?'",
                    "current_exercise": "Ask: 'What does your current exercise routine look like?'",
                    "current_sleep": "Ask: 'How are your sleep habits? How many hours do you typically get per night?'",
                    "current_eating": "Ask: 'What are your current eating habits like? Walk me through a typical day.'",
                    "free_time": "Ask: 'What do you like to do in your free time?'"
                }
                
                result["context"] = f"""Discovery - next question: {next_topic}
Covered: {', '.join(asked)} ({len(asked)}/5)
Remaining: {', '.join(next_questions)}

Acknowledge their response warmly, then ask:
{question_prompts.get(next_topic, 'Ask next discovery question')}"""
        
        elif self.state == SessionState.GOALS:
            goal_candidate = user_input.strip()

            if is_likely_goal(goal_candidate):
                self.session_data["current_goal"] = goal_candidate
                self.session_data["goals"].append(goal_candidate)
                self.session_data["smart_refinement_attempts"] = 0
                
                smart_eval = self.evaluate_smart_goal(goal_candidate)
                self.session_data["goal_smart_analysis"] = smart_eval
                
                if smart_eval["is_smart"]:
                    self._store_completed_goal(confidence=None)
                    result["next_state"] = SessionState.CONFIDENCE_CHECK
                    result["context"] = f"Goal is SMART! Celebrate.\nGoal: {goal_candidate}"
                else:
                    result["next_state"] = SessionState.CHECK_SMART
                    missing = ", ".join(smart_eval["missing_criteria"])
                    result["context"] = f"""SMART Analysis:
Goal: "{goal_candidate}"
Is SMART: No
Missing: {missing}
Suggestions: {smart_eval['suggestions']}

Explain what's missing and guide refinement."""
            else:
                result["context"] = "Not a clear goal. Ask them to describe what they'd like to achieve."
        
        elif self.state == SessionState.CHECK_SMART:
            smart_analysis = self.session_data.get("goal_smart_analysis", {})
            is_smart = smart_analysis.get("is_smart", False)
            
            if is_smart:
                self._store_completed_goal(confidence=None)
                result["next_state"] = SessionState.CONFIDENCE_CHECK
                result["context"] = f"Goal is SMART! Celebrate and ask for confidence level."
            else:
                result["next_state"] = SessionState.REFINE_GOAL
                missing = ", ".join(smart_analysis.get("missing_criteria", []))
                suggestions = smart_analysis.get("suggestions", "")
                result["context"] = f"""Goal needs refinement.
Missing: {missing}
Suggestions: {suggestions}

Guide them to make it more SMART. Be specific about what's missing."""
        
        elif self.state == SessionState.REFINE_GOAL:
            goal_candidate = user_input.strip()
            
            # First, check if coach summarized a refined goal in their last response
            refined_from_coach = None
            if self.session_data.get("last_coach_response"):
                refined_from_coach = extract_refined_goal_from_coach_response(
                    self.session_data["last_coach_response"],
                    user_input
                )
                if refined_from_coach:
                    self._log_debug(f"Extracted refined goal from coach: '{refined_from_coach}'")
            
            # Check if user is confirming the coach's refined goal
            user_confirming = any(phrase in user_lower for phrase in [
                'yes', 'yeah', 'yep', 'correct', 'right', 'that\'s right', 
                'thats right', 'exactly', 'perfect', 'sounds good'
            ])
            
            # If coach stated a refined goal and user confirmed it, use that
            if refined_from_coach and user_confirming and len(user_input.split()) <= 3:
                self._log_debug(f"User confirmed coach's refined goal: '{refined_from_coach}'")
                self.session_data["current_goal"] = refined_from_coach
                self.session_data["smart_refinement_attempts"] += 1
                
                if self.session_data["goals"]:
                    self.session_data["goals"][-1] = refined_from_coach
                
                smart_eval = self.evaluate_smart_goal(refined_from_coach)
                self.session_data["goal_smart_analysis"] = smart_eval
                
                if smart_eval["is_smart"]:
                    self._store_completed_goal(confidence=None)
                    result["next_state"] = SessionState.CONFIDENCE_CHECK
                    result["context"] = f"Refined goal is SMART: '{refined_from_coach}'\nAsk for confidence level (1-10 scale)."
                else:
                    result["context"] = f"Goal refined to: '{refined_from_coach}' but still needs work.\nContinue helping them make it more specific."
                return result
            
            # Use utility to extract refined goal from coach response (for auto-extraction)
            if self.session_data.get("last_coach_response") and not user_confirming:
                refined_goal = extract_refined_goal_from_coach_response(
                    self.session_data["last_coach_response"],
                    user_input
                )
                
                if refined_goal:
                    self._log_debug(f"Auto-extracted refined goal: '{refined_goal}'")
                    self.session_data["current_goal"] = refined_goal
                    self.session_data["smart_refinement_attempts"] += 1
                    
                    if self.session_data["goals"]:
                        self.session_data["goals"][-1] = refined_goal
                    
                    smart_eval = self.evaluate_smart_goal(refined_goal)
                    self.session_data["goal_smart_analysis"] = smart_eval
                    
                    if smart_eval["is_smart"]:
                        self._store_completed_goal(confidence=None)
                        result["next_state"] = SessionState.CONFIDENCE_CHECK
                        result["context"] = f"Refined goal is SMART: '{refined_goal}'\nAsk for confidence level (1-10 scale)."
                        return result
                    else:
                        result["context"] = f"Goal refined to: '{refined_goal}' but still needs work.\nContinue helping them make it more specific."
                        return result
            
            # Use utility to check if coach accepted goal
            coach_accepted = False
            if self.session_data.get("last_coach_response"):
                coach_accepted = check_coach_goal_acceptance(self.session_data["last_coach_response"])
            
            # Use utility to validate goal statement
            looks_like_goal = is_goal_statement(goal_candidate)
            
            moving_forward_phrases = [
                'notes', 'calendar', 'reminder', 'app', 'track', 'write down',
                'thanks', 'thank you', 'sounds good', 'perfect', 'great',
                'see you', 'bye', 'goodbye', 'todo list', 'planner'
            ]
            is_moving_forward = any(phrase in user_lower for phrase in moving_forward_phrases)
            
            if ((is_moving_forward or coach_accepted) and self.session_data["current_goal"]):
                if not self.session_data["goal_details"]:
                    self._store_completed_goal(confidence=8)
                
                if is_moving_forward and any(phrase in user_lower for phrase in ['todo', 'calendar', 'reminder', 'track', 'note']):
                    result["next_state"] = SessionState.REMEMBER_GOAL
                    result["context"] = f"""User described tracking method: "{user_input}"
Goal: "{self.session_data['current_goal']}"
Acknowledge their tracking plan and ask if there's anything else before wrapping up."""
                else:
                    result["next_state"] = SessionState.CONFIDENCE_CHECK
                    result["context"] = f"""Goal accepted: "{self.session_data['current_goal']}"
Ask for confidence level (1-10 scale)."""
            
            elif looks_like_goal:
                is_question = any(indicator in goal_candidate.lower() for indicator in ['?', 'how about', 'what if', 'maybe', 'would', 'could']) or goal_candidate.endswith('?')
                
                if is_question:
                    result["context"] = "User asking a question. Answer and help them finalize the goal statement."
                    return result
                
                # Use utility to enhance goal with details
                current_goal = self.session_data.get("current_goal", "")
                if current_goal:
                    enhanced = enhance_goal_with_details(current_goal, goal_candidate)
                    self.session_data["current_goal"] = enhanced
                else:
                    self.session_data["current_goal"] = goal_candidate
                
                self.session_data["smart_refinement_attempts"] += 1
                
                if self.session_data["goals"]:
                    self.session_data["goals"][-1] = self.session_data["current_goal"]
                
                smart_eval = self.evaluate_smart_goal(self.session_data["current_goal"])
                self.session_data["goal_smart_analysis"] = smart_eval
                
                if smart_eval["is_smart"]:
                    # Clean up the goal with LLM before storing
                    if self.llm_client:
                        context = {
                            "confidence": self.session_data.get("confidence_level"),
                            "discovery": self.session_data.get("discovery", {})
                        }
                        from utils.goal_parser import reword_goal_with_llm
                        cleaned_goal = reword_goal_with_llm(
                            self.session_data["current_goal"], 
                            self.llm_client, 
                            context
                        )
                        self._log_debug(f"Cleaned assembled goal from '{self.session_data['current_goal']}' to '{cleaned_goal}'")
                        self.session_data["current_goal"] = cleaned_goal
                        if self.session_data["goals"]:
                            self.session_data["goals"][-1] = cleaned_goal
                    
                    self._store_completed_goal(confidence=None)
                    result["next_state"] = SessionState.CONFIDENCE_CHECK
                    result["context"] = f"Refined goal is SMART: '{self.session_data['current_goal']}'\nAsk for confidence level."
                else:
                    missing = ", ".join(smart_eval["missing_criteria"])
                    attempts = self.session_data["smart_refinement_attempts"]
                    
                    if attempts >= 4:
                        # Clean up the goal with LLM before storing
                        if self.llm_client:
                            context = {
                                "confidence": self.session_data.get("confidence_level"),
                                "discovery": self.session_data.get("discovery", {})
                            }
                            from utils.goal_parser import reword_goal_with_llm
                            cleaned_goal = reword_goal_with_llm(
                                self.session_data["current_goal"], 
                                self.llm_client, 
                                context
                            )
                            self._log_debug(f"Cleaned assembled goal from '{self.session_data['current_goal']}' to '{cleaned_goal}'")
                            self.session_data["current_goal"] = cleaned_goal
                            if self.session_data["goals"]:
                                self.session_data["goals"][-1] = cleaned_goal
                        
                        self._store_completed_goal(confidence=None)
                        result["next_state"] = SessionState.CONFIDENCE_CHECK
                        result["context"] = f"After {attempts} attempts, move forward with: '{self.session_data['current_goal']}'\nAsk for confidence."
                    else:
                        result["next_state"] = SessionState.REFINE_GOAL
                        result["context"] = f"""Refinement attempt {attempts}.
Goal: "{self.session_data['current_goal']}"
Still missing: {missing}

Ask specific question to get the missing piece. What exactly do they need to add?"""
            else:
                if any(phrase in user_lower for phrase in ['stick with', 'keep', 'thats all', "that's all"]):
                    if self.session_data["current_goal"]:
                        self._store_completed_goal(confidence=None)
                        result["next_state"] = SessionState.CONFIDENCE_CHECK
                        result["context"] = f"User keeping: '{self.session_data['current_goal']}'. Check confidence."
                    else:
                        result["context"] = "Encourage them to state a goal."
                else:
                    result["context"] = "Ask user to refine their goal."
        
        elif self.state == SessionState.CONFIDENCE_CHECK:
            confidence = extract_number(user_input)
            if confidence:
                self.session_data["confidence_level"] = confidence
                
                if self.session_data["goal_details"]:
                    self.session_data["goal_details"][-1]["confidence"] = confidence
                
                if confidence <= 7:
                    result["next_state"] = SessionState.LOW_CONFIDENCE
                    result["context"] = f"Low confidence ({confidence}/10). Explore what would help increase it."
                else:
                    result["next_state"] = SessionState.HIGH_CONFIDENCE
                    result["context"] = f"High confidence ({confidence}/10). Move to asking about more goals."
            else:
                result["context"] = "Ask for numeric confidence (1-10)"
        
        elif self.state == SessionState.LOW_CONFIDENCE:
            if "rework" in user_lower or "change" in user_lower or "different" in user_lower:
                result["next_state"] = SessionState.GOALS
                result["context"] = "User wants to rework goal. Ask what they'd like to focus on instead."
            else:
                result["next_state"] = SessionState.ASK_MORE_GOALS
                result["context"] = "Acknowledge concerns. Move to asking about more goals."
        
        elif self.state == SessionState.HIGH_CONFIDENCE:
            result["next_state"] = SessionState.ASK_MORE_GOALS
            result["context"] = "High confidence confirmed. Ask if they want to set another goal."
        
        elif self.state == SessionState.ASK_MORE_GOALS:
            wants_more = any(word in user_lower for word in ["yes", "yeah", "yep", "sure", "another", "one more", "i'd like", "i want"])
            no_more = any(word in user_lower for word in ["no", "nope", "just", "only", "focus on", "stick with", "that's all", "thats all"])
            
            # Check if user mentioned tracking method
            tracking_methods = ['calendar', 'reminder', 'app', 'note', 'journal', 'planner', 'todo', 'phone', 'alarm', 'schedule', 'write', 'set']
            user_described_tracking = any(method in user_lower for method in tracking_methods)
            
            if user_described_tracking:
                self.session_data["tracking_method_discussed"] = True
                result["next_state"] = SessionState.END_SESSION
                result["context"] = f"""User described tracking method: "{user_input}"
Acknowledge their plan and provide warm closing. Confirm next session is in 1 week."""
                return result
            
            coach_wrapped_up = False
            if self.session_data.get("last_coach_response"):
                coach_lower = self.session_data["last_coach_response"].lower()
                wrapping_phrases = [
                    'good luck', 'have a great week',
                    "i'm really looking forward", 'looking forward to hearing',
                    'see you next', "i'll see you",
                    'have a wonderful'
                ]
                coach_wrapped_up = any(phrase in coach_lower for phrase in wrapping_phrases)
            
            # Check if coach asked about tracking
            coach_asked_tracking = False
            if self.session_data.get("last_coach_response"):
                coach_lower = self.session_data["last_coach_response"].lower()
                tracking_questions = [
                    'how will you keep track',
                    'how will you track',
                    'how will you remember',
                    'remind yourself',
                    'system or reminder'
                ]
                coach_asked_tracking = any(phrase in coach_lower for phrase in tracking_questions)
            
            user_confirming_end = user_lower in ['are we done', 'is that it', 'are we finished', 'ok', 'thanks', 'thank you']
            
            if wants_more and "focus" not in user_lower:
                result["next_state"] = SessionState.GOALS
                result["context"] = "Great! Ask about their next goal."
            elif coach_wrapped_up and (no_more or user_confirming_end):
                result["next_state"] = SessionState.END_SESSION
                result["context"] = "Session complete. Confirm and close warmly."
            elif no_more or "focus" in user_lower:
                # Check if tracking was already discussed
                tracking_discussed = self.session_data.get("tracking_method_discussed", False)
                
                if not tracking_discussed and conversation_history:
                    for msg in conversation_history[-10:]:
                        if msg.get('role') == 'assistant':
                            content = msg.get('content', '').lower()
                            if any(phrase in content for phrase in ['how will you remember', 'how will you track', 'remind yourself', 'system or reminder']):
                                tracking_discussed = True
                                self.session_data["tracking_method_discussed"] = True
                                break
                
                # If coach just asked about tracking and user said no to more goals, wrap up
                if coach_asked_tracking and no_more:
                    result["next_state"] = SessionState.END_SESSION
                    result["context"] = "User confirmed no more goals after tracking question. Provide brief warm closing."
                elif tracking_discussed or coach_wrapped_up:
                    result["next_state"] = SessionState.END_SESSION
                    result["context"] = "No more goals and tracking discussed. Wrap up session."
                else:
                    result["next_state"] = SessionState.REMEMBER_GOAL
                    result["context"] = "No more goals. Ask how they'll track/remember their goal."
            else:
                result["context"] = "Ask user to clarify: would they like to set another goal or focus on this one?"
        
        elif self.state == SessionState.REMEMBER_GOAL:
            tracking_methods = ['calendar', 'reminder', 'app', 'note', 'journal', 'planner', 'todo', 'phone', 'alarm', 'schedule', 'write', 'set']
            described_tracking = any(method in user_lower for method in tracking_methods)
            
            if described_tracking:
                self.session_data["tracking_method_discussed"] = True
            
            # Check if coach asked a wrap-up question
            coach_asking_wrap_up = False
            if self.session_data.get("last_coach_response"):
                coach_lower = self.session_data["last_coach_response"].lower()
                wrap_up_questions = [
                    'anything else', 'is there anything else',
                    'before we wrap', 'before we finish',
                    'ready to wrap', 'all set'
                ]
                coach_asking_wrap_up = any(phrase in coach_lower for phrase in wrap_up_questions)
            
            # Check if coach has said goodbye
            coach_said_goodbye = False
            if self.session_data.get("last_coach_response"):
                coach_lower = self.session_data["last_coach_response"].lower()
                goodbye_phrases = [
                    'best of luck', 'good luck', 'have a wonderful', 
                    'see you at our next session', 'see you next week', 
                    'talk to you next', 'until next session',
                    "i'll see you", "see you in one week",
                    'excited for you to try', 'take care',
                    'looking forward to hearing'
                ]
                coach_said_goodbye = any(phrase in coach_lower for phrase in goodbye_phrases)
            
            # Check if user is ready to end
            user_ready_to_end = any(phrase in user_lower for phrase in [
                'no', 'nope', 'nah', "that's all", "thats all",
                'nothing else', 'im good', "i'm good", 'all set',
                'ready', 'see you', 'bye', 'thanks'
            ])
            
            # End conditions: coach said goodbye OR (coach asked wrap-up AND user said no)
            if coach_said_goodbye or (coach_asking_wrap_up and user_ready_to_end):
                result["next_state"] = SessionState.END_SESSION
                result["context"] = f"""Session wrapping up naturally.
Goal(s): {', '.join([g['goal'] for g in self.session_data.get('goal_details', [])])}

Provide warm closing with brief summary. Confirm next session is in 1 week."""
            # If tracking described but no wrap-up yet, ask about anything else
            elif described_tracking and not coach_asking_wrap_up:
                result["context"] = "Acknowledge tracking plan and ask: 'Is there anything else you'd like to talk about before we wrap up today?'"
            # If no tracking mentioned yet, ask about it
            elif not described_tracking:
                result["context"] = "Ask about their tracking plan. How will they remember their goal?"
            else:
                result["context"] = "Acknowledge and prepare to wrap up session."
        
        elif self.state == SessionState.END_SESSION:
            # Session is complete - stay in END_SESSION
            result["context"] = "Session complete. Provide brief, warm confirmation if needed, but session is ending."
            
            if not self.session_data.get("goal_details"):
                result["next_state"] = SessionState.GOALS
                result["context"] = "ERROR: No goals stored. Let's make sure we have a clear goal before ending."
        
        if result["next_state"]:
            self._log_debug(f"Next state will be: {result['next_state'].value}")
        
        return result
    
    def _store_completed_goal(self, confidence: int = None):
        """Store a completed goal with its details using utility function"""
        if not self.session_data["current_goal"]:
            return
        
        # Prepare context for goal rewording
        context = {
            "confidence": confidence or self.session_data.get("confidence_level"),
            "discovery": self.session_data.get("discovery", {})
        }
        
        # Use the utility function to store the goal (with LLM rewording)
        was_stored = store_goal(
            goal_text=self.session_data["current_goal"],
            existing_goals=self.session_data["goal_details"],
            confidence=confidence,
            smart_analysis=self.session_data.get("goal_smart_analysis"),
            refinement_attempts=self.session_data.get("smart_refinement_attempts", 0),
            session_number=1,
            similarity_threshold=50,
            llm_client=self.llm_client,  # Pass LLM client for rewording
            context=context
        )
        
        if was_stored:
            # Update current_goal with the reworded version
            if self.session_data["goal_details"]:
                self.session_data["current_goal"] = self.session_data["goal_details"][-1]["goal"]
                self._log_debug(f"Stored reworded goal: {self.session_data['current_goal']}")

    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of session data"""
        return {
            "current_state": self.state.value,
            "session_data": self.session_data,
            "duration_turns": self.session_data["turn_count"],
            "goals_summary": format_goals_summary(self.session_data["goal_details"])
        }
    
    def save_session(self, filename: str = None, conversation_history: list = None):
        """Save session using unified storage format and database"""
        self._log_debug("Saving session with unified format")
        
        # Prepare discovery data
        discovery = {
            "general_about": self.session_data["discovery"].get("general_about"),
            "current_exercise": self.session_data["discovery"].get("current_exercise"),
            "current_sleep": self.session_data["discovery"].get("current_sleep"),
            "current_eating": self.session_data["discovery"].get("current_eating"),
            "free_time_activities": self.session_data["discovery"].get("free_time_activities")
        }
        
        # Prepare goals list
        goals = []
        for goal_detail in self.session_data.get("goal_details", []):
            goals.append({
                "goal": goal_detail.get("goal"),
                "confidence": goal_detail.get("confidence"),
                "stress": None,
                "session_created": 1,
                "status": "active",
                "created_at": self.session_data.get("session_start")
            })
        
        # Prepare session metadata
        session_metadata = {
            "turn_count": self.session_data.get("turn_count"),
            "current_goal": self.session_data.get("current_goal"),
            "program_questions_asked": self.session_data.get("program_questions_asked", []),
            "tracking_method_discussed": self.session_data.get("tracking_method_discussed", False)
        }
        
        # Build full data structure for database
        full_data = {
            "user_profile": {
                "uid": self.uid,
                "name": self.session_data.get("user_name"),
                "goals": goals,
                "discovery_questions": discovery
            },
            "session_info": {
                "session_number": 1,
                "current_state": self.state.value,
                "metadata": session_metadata
            },
            "chat_history": conversation_history or []
        }
        
        # Save to PostgreSQL database
        if save_session_to_db(self.uid, 1, full_data):
            self._log_debug(f"Session saved to database for UID: {self.uid}")
        else:
            self._log_debug("Warning: Failed to save to database")
        
        # Also save to file (backup/legacy support)
        filename = save_unified_session(
            uid=self.uid,
            user_name=self.session_data.get("user_name"),
            session_number=1,
            current_state=self.state.value,
            discovery=discovery,
            goals=goals,
            session_metadata=session_metadata,
            conversation_history=conversation_history,
            filename=filename
        )
        
        self._log_debug(f"Session saved to {filename}")
        return filename
    
    def load_session(self, filename: str):
        """Load session data from unified format"""
        from utils.unified_storage import load_unified_session
        
        data = load_unified_session(filename)
        
        # Extract user profile
        profile = data.get("user_profile", {})
        session_info = data.get("session_info", {})
        
        # Restore state
        self.state = SessionState(session_info.get("current_state", "greetings"))
        self.uid = profile.get("uid")
        
        # Restore session data
        self.session_data["uid"] = self.uid
        self.session_data["user_name"] = profile.get("name")
        
        # Restore discovery
        discovery_data = profile.get("discovery_questions", {})
        self.session_data["discovery"] = {
            "general_about": discovery_data.get("tell_me_about_yourself"),
            "current_exercise": discovery_data.get("exercise_routine"),
            "current_sleep": discovery_data.get("sleep_habits"),
            "current_eating": discovery_data.get("eating_habits"),
            "free_time_activities": discovery_data.get("free_time"),
            "questions_asked": []
        }
        
        # Restore goals
        goals = profile.get("goals", [])
        self.session_data["goal_details"] = []
        for goal in goals:
            if goal.get("session_created") == 1:
                self.session_data["goal_details"].append({
                    "goal": goal.get("goal"),
                    "confidence": goal.get("confidence"),
                    "smart_analysis": None,
                    "refinement_attempts": 0
                })
        
        # Restore metadata
        metadata = session_info.get("metadata", {})
        self.session_data["turn_count"] = metadata.get("turn_count", 0)
        self.session_data["current_goal"] = metadata.get("current_goal")
        self.session_data["program_questions_asked"] = metadata.get("program_questions_asked", [])
        self.session_data["tracking_method_discussed"] = metadata.get("tracking_method_discussed", False)
        
        self._log_debug(f"Session loaded from {filename}")
        
        return data.get("chat_history", [])