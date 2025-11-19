from enum import Enum
from typing import Dict, Any, Optional, Tuple
import json
import os
from datetime import datetime
import re

from utils.smart_evaluation import evaluate_smart_goal_with_llm, heuristic_smart_check
from utils.session_storage import save_session_data, load_session_data
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
    
    def __init__(self, program_info_file: str = "program_info.txt", llm_client=None):
        self.state = SessionState.GREETINGS
        self.session_data = {
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
        
    def set_llm_client(self, llm_client):
        """Set the LLM client for SMART goal evaluation"""
        self.llm_client = llm_client
    
    def evaluate_smart_goal(self, goal: str) -> Dict[str, Any]:
        """Use LLM to evaluate if a goal is SMART"""
        if not self.llm_client:
            return heuristic_smart_check(goal)
        
        return evaluate_smart_goal_with_llm(goal, self.llm_client)
    
    def _heuristic_smart_check(self, goal: str) -> Dict[str, Any]:
        """Simple heuristic-based SMART check as fallback"""
        return heuristic_smart_check(goal)
    
    def get_state(self) -> SessionState:
        return self.state
    
    def set_state(self, new_state: SessionState):
        self.state = new_state
    
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
            
            goal_keywords = ["want to", "goal is", "goal:", "would like to", "hoping to", "trying to", "plan to", "i want", "my goal"]
            user_stating_goal = any(phrase in user_lower for phrase in goal_keywords)
            
            min_discovery_complete = len(asked) >= 3
            
            if user_stating_goal and len(user_input.split()) > 4 and min_discovery_complete:
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
            
            # Check if coach is refining/specifying the goal
            if self.session_data.get("last_coach_response"):
                coach_response = self.session_data["last_coach_response"]
                coach_lower = coach_response.lower()
                
                refined_goal_indicators = [
                    "so you're thinking",
                    "okay, so",
                    "perfect, so",
                    "so your goal is",
                    "that sounds like",
                    "let me make sure i understand",
                    "so monday"
                ]
                
                is_coach_summarizing = any(indicator in coach_lower for indicator in refined_goal_indicators)
                
                if is_coach_summarizing:
                    hours_match = re.search(r'(\d+)\s*hours?', coach_lower)
                    hours = hours_match.group(1) if hours_match else None
                    
                    freq_match = re.search(r'(\d+)\s*(times?|days?|nights?)\s*(per |a |this |each )?week', coach_lower)
                    frequency = freq_match.group(1) if freq_match else None
                    
                    days_mentioned = []
                    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    
                    for day in day_names:
                        if day in user_lower:
                            days_mentioned.append(day.capitalize())
                    
                    if not days_mentioned:
                        for day in day_names:
                            if day in coach_lower:
                                days_mentioned.append(day.capitalize())
                    
                    if hours and (frequency or days_mentioned):
                        if days_mentioned and len(days_mentioned) >= 2:
                            if len(days_mentioned) == 2:
                                days_str = f"{days_mentioned[0]} and {days_mentioned[1]}"
                            else:
                                days_str = ', '.join(days_mentioned[:-1]) + f", and {days_mentioned[-1]}"
                            refined_goal = f"Get {hours} hours of sleep on {days_str} each week"
                        elif frequency:
                            refined_goal = f"Get {hours} hours of sleep {frequency} nights per week"
                        else:
                            refined_goal = None
                        
                        if refined_goal:
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
            
            # Check if coach accepted goal
            coach_accepted = False
            if self.session_data.get("last_coach_response"):
                coach_response_lower = self.session_data["last_coach_response"].lower()
                
                coach_acceptance_patterns = [
                    r"you've got a clear.*goal",
                    r"that's a solid goal",
                    r"solid starting point",
                    r"fantastic.*goal",
                    r"excellent.*goal", 
                    r"perfect.*goal",
                    r"great goal",
                    r"this is going to",
                    r"you're all set",
                    r"how will you remind",
                    r"how will you track",
                    r"what.*remind yourself",
                    r"on a scale.*confident"
                ]
                
                coach_accepted = any(re.search(pattern, coach_response_lower) for pattern in coach_acceptance_patterns)
            
            non_goal_phrases = [
                'no', 'yes', 'maybe', 'i dont know', "i don't know", 'not sure',
                'just want to stick', 'thats all', "that's all", 'nothing else',
                'im good', "i'm good", 'no more', 'nope', 'nah', 'keep it'
            ]
            
            goal_lower = goal_candidate.lower()
            is_likely_goal = (
                len(goal_candidate.split()) > 3 and
                not any(phrase in goal_lower for phrase in non_goal_phrases) and
                not goal_lower.startswith(('no ', 'yes ', 'maybe '))
            )
            
            moving_forward_phrases = [
                'notes', 'calendar', 'reminder', 'app', 'track', 'write down',
                'thanks', 'thank you', 'sounds good', 'perfect', 'great',
                'see you', 'bye', 'goodbye', 'todo list', 'planner'
            ]
            is_moving_forward = any(phrase in goal_lower for phrase in moving_forward_phrases)
            
            if ((is_moving_forward or coach_accepted) and self.session_data["current_goal"]):
                if not self.session_data["goal_details"]:
                    self._store_completed_goal(confidence=8)
                
                if is_moving_forward and any(phrase in goal_lower for phrase in ['todo', 'calendar', 'reminder', 'track', 'note']):
                    result["next_state"] = SessionState.REMEMBER_GOAL
                    result["context"] = f"""User described tracking method: "{user_input}"
Goal: "{self.session_data['current_goal']}"
Acknowledge their tracking plan and ask if there's anything else before wrapping up."""
                else:
                    result["next_state"] = SessionState.CONFIDENCE_CHECK
                    result["context"] = f"""Goal accepted: "{self.session_data['current_goal']}"
Ask for confidence level (1-10 scale)."""
            
            elif is_likely_goal:
                is_question = any(indicator in goal_candidate.lower() for indicator in ['?', 'how about', 'what if', 'maybe', 'would', 'could']) or goal_candidate.endswith('?')
                
                if is_question:
                    result["context"] = "User asking a question. Answer and help them finalize the goal statement."
                    return result
                
                current_goal = self.session_data.get("current_goal", "")
                
                time_indicators = ['week', 'month', 'day', 'by', 'within', 'in']
                number_indicators = re.findall(r'\d+', goal_candidate)
                
                if any(ind in goal_lower for ind in time_indicators) or number_indicators:
                    if current_goal:
                        enhanced_goal = f"{current_goal} {goal_candidate}"
                        self.session_data["current_goal"] = enhanced_goal
                    else:
                        self.session_data["current_goal"] = goal_candidate
                else:
                    self.session_data["current_goal"] = goal_candidate
                
                self.session_data["smart_refinement_attempts"] += 1
                
                if self.session_data["goals"]:
                    self.session_data["goals"][-1] = self.session_data["current_goal"]
                
                smart_eval = self.evaluate_smart_goal(self.session_data["current_goal"])
                self.session_data["goal_smart_analysis"] = smart_eval
                
                if smart_eval["is_smart"]:
                    self._store_completed_goal(confidence=None)
                    result["next_state"] = SessionState.CONFIDENCE_CHECK
                    result["context"] = f"Refined goal is SMART: '{self.session_data['current_goal']}'\nAsk for confidence level."
                else:
                    missing = ", ".join(smart_eval["missing_criteria"])
                    attempts = self.session_data["smart_refinement_attempts"]
                    
                    if attempts >= 4:
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
                if any(phrase in goal_lower for phrase in ['stick with', 'keep', 'thats all', "that's all"]):
                    if self.session_data["current_goal"]:
                        self._store_completed_goal(confidence=None)
                        result["next_state"] = SessionState.CONFIDENCE_CHECK
                        result["context"] = f"User keeping: '{self.session_data['current_goal']}'. Check confidence."
                    else:
                        result["context"] = "Encourage them to state a goal."
                else:
                    result["context"] = "Ask user to refine their goal."
        
        elif self.state == SessionState.CONFIDENCE_CHECK:
            try:
                confidence = extract_number(user_input)
                if confidence:
                    confidence = int(numbers[0])
                    self.session_data["confidence_level"] = confidence
                    
                    if self.session_data["goal_details"]:
                        self.session_data["goal_details"][-1]["confidence"] = confidence
                    
                    if confidence <= 7:
                        result["next_state"] = SessionState.LOW_CONFIDENCE
                    else:
                        result["next_state"] = SessionState.HIGH_CONFIDENCE
                else:
                    result["context"] = "Ask for numeric confidence (1-10)"
            except:
                result["context"] = "Ask for numeric confidence (1-10)"
        
        elif self.state == SessionState.LOW_CONFIDENCE:
            if "rework" in user_lower or "change" in user_lower or "different" in user_lower:
                result["next_state"] = SessionState.GOALS
            else:
                result["next_state"] = SessionState.ASK_MORE_GOALS
        
        elif self.state == SessionState.HIGH_CONFIDENCE:
            result["next_state"] = SessionState.ASK_MORE_GOALS
        
        elif self.state == SessionState.ASK_MORE_GOALS:
            wants_more = any(word in user_lower for word in ["yes", "yeah", "yep", "sure", "another", "one more", "i'd like", "i want"])
            no_more = any(word in user_lower for word in ["no", "nope", "just", "only", "focus on", "stick with", "that's all", "thats all"])
            
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
            
            user_confirming_end = user_lower in ['are we done', 'is that it', 'are we finished', 'ok', 'thanks', 'thank you']
            
            if wants_more:
                result["next_state"] = SessionState.GOALS
                result["context"] = "Great! Ask about their next goal."
            elif coach_wrapped_up and (no_more or user_confirming_end):
                result["next_state"] = SessionState.END_SESSION
                result["context"] = "Session complete. Confirm and close warmly."
            elif no_more:
                tracking_discussed = self.session_data.get("tracking_method_discussed", False)
                
                if conversation_history:
                    for msg in conversation_history[-10:]:
                        if msg.get('role') == 'assistant':
                            content = msg.get('content', '').lower()
                            if any(phrase in content for phrase in ['how will you remember', 'how will you track', 'remind yourself', 'system or reminder']):
                                tracking_discussed = True
                                self.session_data["tracking_method_discussed"] = True
                                break
                
                if tracking_discussed or coach_wrapped_up:
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
        
        return result
    
    def _store_completed_goal(self, confidence: int = None):
        """Store a completed goal with its details"""
        if self.session_data["current_goal"]:
            current_goal = self.session_data["current_goal"]
            
            is_question = '?' in current_goal or any(phrase in current_goal.lower() for phrase in ['how about', 'what if', 'maybe we', 'could we'])
            is_too_short = len(current_goal.split()) < 4
            
            if is_question or is_too_short:
                return
            
            existing_goals = [g["goal"] for g in self.session_data["goal_details"]]
            
            similar_exists = False
            for existing in existing_goals:
                if existing[:50] == current_goal[:50]:
                    similar_exists = True
                    for goal_entry in self.session_data["goal_details"]:
                        if goal_entry["goal"][:50] == current_goal[:50]:
                            if len(current_goal) > len(goal_entry["goal"]):
                                goal_entry["goal"] = current_goal
                                goal_entry["smart_analysis"] = self.session_data.get("goal_smart_analysis")
                                goal_entry["refinement_attempts"] = self.session_data.get("smart_refinement_attempts", 0)
                            if confidence is not None:
                                goal_entry["confidence"] = confidence
                            break
                    break
            
            if not similar_exists and current_goal not in existing_goals:
                goal_entry = {
                    "goal": current_goal,
                    "confidence": confidence,
                    "smart_analysis": self.session_data.get("goal_smart_analysis"),
                    "refinement_attempts": self.session_data.get("smart_refinement_attempts", 0)
                }
                self.session_data["goal_details"].append(goal_entry)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of session data"""
        return {
            "current_state": self.state.value,
            "session_data": self.session_data,
            "duration_turns": self.session_data["turn_count"]
        }
    
    def save_session(self, filename: str = None, conversation_history: list = None):
        """Save session data to JSON file"""
        return save_session_data(
            state_value=self.state.value,
            session_data=self.session_data,
            conversation_history=conversation_history,
            filename=filename,
            session_prefix="session1"
        )
    
    def load_session(self, filename: str):
        """Load session data from JSON file"""
        data = load_session_data(filename)
        
        self.state = SessionState(data["state"])
        self.session_data = data["session_data"]
        
        return data.get("conversation_history", [])