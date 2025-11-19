"""
Base class for session-based RAG chatbots.
Provides common functionality for all coaching sessions.
"""
from rag_dynamic import UnifiedRAGChatbot
from typing import Dict, Any, List
from abc import ABC, abstractmethod
import time


class BaseSessionRAGChatbot(UnifiedRAGChatbot, ABC):
    """
    Base class for session-based coaching chatbots.
    Provides common functionality shared across all sessions.
    Session managers remain unchanged in subclasses.
    """
    
    def __init__(self, model='claude-sonnet-4.5', top_k=3, 
                 recent_messages=6, relevant_history_count=4, 
                 validate_constraints=True):
        """
        Initialize base session chatbot.
        
        Args:
            model: LLM model to use
            top_k: Number of RAG examples to retrieve
            recent_messages: Number of recent messages to include in context
            relevant_history_count: Number of relevant older messages to include
            validate_constraints: Whether to validate response constraints
        """
        super().__init__(model=model, top_k=top_k)
        
        self.recent_messages = recent_messages
        self.relevant_history_count = relevant_history_count
        self.validate_constraints = validate_constraints
        self.session_manager = None  # Set by subclass
    
    def _create_llm_evaluator(self):
        """Create an LLM client wrapper for SMART goal evaluation"""
        class LLMEvaluator:
            def __init__(self, parent):
                self.parent = parent
            
            def evaluate_goal(self, prompt):
                """Quick evaluation call to LLM for SMART goal checking"""
                max_retries = 3
                retry_delay = 1
                
                for attempt in range(max_retries):
                    try:
                        if self.parent.model_info['provider'] == 'anthropic':
                            model_id = self.parent.model_info.get('model_id', self.parent.model)
                            response = self.parent.anthropic_client.messages.create(
                                model=model_id,
                                max_tokens=1000,
                                temperature=0.1,
                                messages=[{
                                    "role": "user",
                                    "content": prompt
                                }]
                            )
                            return response.content[0].text
                        else:  # OpenAI
                            response = self.parent.openai_client.chat.completions.create(
                                model=self.parent.model,
                                messages=[
                                    {"role": "system", "content": "You are a SMART goal evaluator. Respond only with valid JSON. Never include markdown formatting."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.1,
                                max_tokens=1000,
                                response_format={"type": "json_object"}
                            )
                            return response.choices[0].message.content
                    except Exception as e:
                        error_str = str(e)
                        if 'overloaded' in error_str.lower() and attempt < max_retries - 1:
                            print(f"\n[API Overloaded during SMART eval - Retrying in {retry_delay}s...]", flush=True)
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
        
        return LLMEvaluator(self)
    
    def _select_relevant_history(self, current_message: str, max_relevant: int = 4):
        """Cherry-pick relevant messages from older history"""
        if len(self.conversation_history) <= self.recent_messages:
            return []
        
        older_history = self.conversation_history[:-self.recent_messages]
        
        if not older_history:
            return []
        
        try:
            relevant_exchanges = []
            
            for i in range(0, len(older_history), 2):
                if i + 1 < len(older_history):
                    user_msg = older_history[i]
                    assistant_msg = older_history[i + 1]
                    
                    if user_msg['role'] == 'user' and assistant_msg['role'] == 'assistant':
                        user_content = user_msg.get('content', '')
                        if user_content is None:
                            user_content = ''
                        
                        user_content_lower = user_content.lower()
                        current_lower = current_message.lower()
                        
                        keywords = ['goal', 'exercise', 'eat', 'sleep', 'weight', 'health', 
                                  'walk', 'run', 'diet', 'nutrition', 'water', 'stress',
                                  'challenge', 'success', 'difficult', 'accomplished']
                        
                        user_keywords = [k for k in keywords if k in user_content_lower]
                        current_keywords = [k for k in keywords if k in current_lower]
                        
                        overlap = set(user_keywords) & set(current_keywords)
                        
                        session_name = self.session_manager.session_data.get('user_name')
                        if session_name:
                            session_name = session_name.lower()
                            has_personal_ref = session_name and (session_name in current_lower or session_name in user_content_lower)
                        else:
                            has_personal_ref = False
                        
                        if overlap or has_personal_ref:
                            relevance_score = len(overlap) + (2 if has_personal_ref else 0)
                            relevant_exchanges.append({
                                'score': relevance_score,
                                'messages': [user_msg, assistant_msg],
                                'index': i
                            })
            
            relevant_exchanges.sort(key=lambda x: x['score'], reverse=True)
            selected = relevant_exchanges[:max_relevant]
            
            selected.sort(key=lambda x: x['index'])
            
            result = []
            for exchange in selected:
                result.extend(exchange['messages'])
            
            return result
            
        except Exception as e:
            return []
    
    def _build_context_messages(self, current_message: str):
        """Build context messages for LLM"""
        messages = []
        
        relevant_old = self._select_relevant_history(current_message, self.relevant_history_count)
        
        if relevant_old:
            messages.append({
                "role": "user",
                "content": "[Earlier conversation context - relevant to current topic]"
            })
            messages.extend(relevant_old)
            messages.append({
                "role": "user", 
                "content": "[End of earlier context - returning to recent conversation]"
            })
        
        if self.conversation_history:
            recent = self.conversation_history[-self.recent_messages:]
            messages.extend(recent)
        
        return messages
    
    def get_base_system_prompt(self) -> str:
        """Get base coaching prompt - same for all sessions"""
        return """You are Nala, a supportive AI health and wellness coach. Your coaching style should be:
- Warm, empathetic, and encouraging
- Ask open-ended questions to promote reflection
- Help users set SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound)
- Acknowledge their feelings and validate their experiences
- Provide actionable suggestions based on their specific situation
- Celebrate their wins and progress
- Keep responses concise and conversational (2-4 sentences)
- Ask only 1 question at a time

CRITICAL ACCURACY RULES:
- NEVER assume, infer, or fill in details the user didn't explicitly state
- If you're unsure about something they said, ASK for clarification
- Repeat back what you heard to confirm accuracy: "So you said X, is that right?"
- Don't do math or count things unless the user gave you exact numbers
- Always verify your understanding before moving forward

CRITICAL WRITING STYLE:
- Write like a human having a natural conversation
- NO markdown formatting (no #, **, *, _, etc.)
- NO emojis (no 😊, 👋, 🌟, etc.)
- NO special characters for emphasis
- Use plain text only
- Sound natural, warm, and conversational
- Write in complete sentences with normal punctuation

CRITICAL PROGRAM CONSTRAINTS:
- This is a 4-session program (Session 1, 2, 3, and 4)
- Sessions happen ONCE PER WEEK - exactly 1 week apart
- There are NO check-ins, calls, emails, or contact between sessions
- You CANNOT promise to "check in", "follow up", "send reminders", or "reach out" between sessions
- The participant is responsible for their own tracking and accountability between sessions
- Next contact will be at the next scheduled weekly session

Instead of promising check-ins, encourage:
- Self-tracking methods (journal, app, calendar reminders)
- Building their own accountability systems
- Support from friends/family
- Looking forward to discussing progress at next week's session"""
    
    def get_system_prompt(self, context):
        """Build system prompt with RAG context and session state"""
        base_prompt = self.get_base_system_prompt()
        
        if context:
            base_prompt += f"\n\n{context}\n\nUse these examples as guidance for your coaching style and responses."
        
        state_prompt = self.session_manager.get_system_prompt_addition()
        if state_prompt:
            base_prompt += f"\n\n--- SESSION CONTEXT ---{state_prompt}"
        
        return base_prompt
    
    def _check_and_warn_constraints(self, response: str) -> str:
        """Check if response violates program constraints"""
        return response
    
    def _call_llm(self, user_message: str, system_prompt: str) -> str:
        """Call LLM API - handles both Anthropic and OpenAI with retry logic"""
        if self.model_info['provider'] == 'anthropic':
            context_messages = self._build_context_messages(user_message)
            context_messages.append({"role": "user", "content": user_message})
            
            model_id = self.model_info.get('model_id', self.model)
            full_response = ""
            
            max_retries = 4
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    with self.anthropic_client.messages.stream(
                        model=model_id,
                        max_tokens=500,
                        temperature=0.7,
                        system=[
                            {
                                "type": "text",
                                "text": system_prompt,
                                "cache_control": {"type": "ephemeral"}
                            }
                        ],
                        messages=context_messages
                    ) as stream:
                        try:
                            for text in stream.text_stream:
                                print(text, end="", flush=True)
                                full_response += text
                        except Exception as stream_err:
                            raise RuntimeError(f"SSE chunk error: {stream_err}")
                    
                    return full_response
                    
                except Exception as e:
                    error_str = str(e)
                    is_server_error = (
                        hasattr(e, "status_code") and
                        isinstance(e.status_code, int) and
                        500 <= e.status_code < 600
                    )
                    
                    if (is_server_error or 'overloaded' in error_str.lower()) and attempt < max_retries - 1:
                        print(f"\n[API Error - Retrying in {retry_delay}s...]", flush=True)
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
            
        else:  # OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            context_messages = self._build_context_messages(user_message)
            messages.extend(context_messages)
            messages.append({"role": "user", "content": user_message})
            
            openai_response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=400
            )
            return openai_response.choices[0].message.content
    
    def generate_response(self, user_message, use_history=True, debug_history=False):
        """Generate response with session management"""
        # Get last coach response for state detection
        last_coach_response = None
        if self.conversation_history:
            for msg in reversed(self.conversation_history):
                if msg['role'] == 'assistant':
                    last_coach_response = msg.get('content', '')
                    break
        
        # Process through session manager
        session_result = self.session_manager.process_user_input(
            user_message,
            last_coach_response=last_coach_response,
            conversation_history=self.conversation_history
        )
        
        # Update state BEFORE generating response
        if session_result["next_state"]:
            self.session_manager.set_state(session_result["next_state"])
        
        # Retrieve examples only if RAG needed
        retrieved_examples = []
        rag_context = ""
        
        if session_result["trigger_rag"]:
            retrieved_examples = self.retrieve(user_message)
            rag_context = self.build_context(retrieved_examples)
        
        # Build system prompt with RAG + session context
        system_prompt = self.get_system_prompt(rag_context)
        
        if session_result["context"]:
            system_prompt += f"\n\n--- ADDITIONAL CONTEXT ---\n{session_result['context']}"
        
        # ALWAYS add memory summary
        memory_summary = self._get_memory_summary()
        if memory_summary:
            system_prompt += f"\n\n--- PERSISTENT MEMORY ---\n{memory_summary}"
        
        # Call LLM
        response = self._call_llm(user_message, system_prompt)
        
        # Validate constraints if enabled
        if self.validate_constraints:
            response = self._check_and_warn_constraints(response)
        
        # Update conversation history
        if use_history:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
        
        return response, retrieved_examples, self.model_info['name']
    
    def save_session(self, filename=None):
        """Save current session including conversation history"""
        return self.session_manager.save_session(filename, self.conversation_history)
    
    def load_session(self, filename):
        """Load session including conversation history"""
        history = self.session_manager.load_session(filename)
        self.conversation_history = history
        return history
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    def _get_memory_summary(self):
        """Generate memory summary - must be implemented by subclass"""
        raise NotImplementedError("Subclass must implement _get_memory_summary")
    
    @abstractmethod
    def get_session_info(self):
        """Get current session state and data - must be implemented by subclass"""
        raise NotImplementedError("Subclass must implement get_session_info")
    
    @abstractmethod
    def reset_session(self):
        """Reset session to beginning - must be implemented by subclass"""
        raise NotImplementedError("Subclass must implement reset_session")