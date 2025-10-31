from rag_dynamic import UnifiedRAGChatbot
from session1 import Session1Manager, SessionState
import os
from dotenv import load_dotenv
import time

load_dotenv()


class SessionBasedRAGChatbot(UnifiedRAGChatbot):
    """
    Extends UnifiedRAGChatbot with session management for structured coaching flows
    """
    
    def __init__(self, model='claude-sonnet-4.5', top_k=3, program_info_file='program_info.txt',
                 recent_messages=6, relevant_history_count=4, validate_constraints=True):
        super().__init__(model=model, top_k=top_k)
        
        self.program_info_file = program_info_file
        self.recent_messages = recent_messages
        self.relevant_history_count = relevant_history_count
        self.validate_constraints = validate_constraints
        
        self.session_manager = Session1Manager(program_info_file=program_info_file)
        self.session_manager.set_llm_client(self._create_llm_evaluator())
    
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
                                  'event', 'wear', 'fit', 'clothes', 'dress', 'outfit']
                        
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
    
    def get_system_prompt(self, context):
        """Override parent to add session-specific context and constraints"""
        base_prompt = """You are Nala, a supportive AI health and wellness coach. Your coaching style should be:
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
- If they say "MW and the weekend", that's 2-3 days, NOT "three times a week"
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
        
        if context:
            base_prompt += f"\n\n{context}\n\nUse these examples as guidance for your coaching style and responses."
        
        state_prompt = self.session_manager.get_system_prompt_addition()
        if state_prompt:
            base_prompt += f"\n\n--- SESSION CONTEXT ---{state_prompt}"
        
        return base_prompt
    
    def generate_response(self, user_message, use_history=True, debug_history=False):
        """Override parent to add session management and smart memory"""
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
            conversation_history=self.conversation_history  # Pass the history
        )
        
        # Update state BEFORE generating response
        if session_result["next_state"]:
            old_state = self.session_manager.get_state().value
            new_state = session_result["next_state"].value
            self.session_manager.set_state(session_result["next_state"])
            
            # Only log significant state changes (left here for help with debugging)
            # if old_state != new_state:
            #     print(f"\n[State: {old_state} → {new_state}]", flush=True)
        
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
        
        # Prepare messages with smart history selection
        if self.model_info['provider'] == 'anthropic':
            context_messages = self._build_context_messages(user_message)
            context_messages.append({"role": "user", "content": user_message})
            
            model_id = self.model_info.get('model_id', self.model)
            full_response = ""
            
            # Retry logic with exponential backoff
            max_retries = 3
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
                        for text in stream.text_stream:
                            print(text, end="", flush=True)
                            full_response += text
                    
                    response = full_response
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_str = str(e)
                    if 'overloaded' in error_str.lower() and attempt < max_retries - 1:
                        print(f"\n[API Overloaded - Retrying in {retry_delay}s...]", flush=True)
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
            response = openai_response.choices[0].message.content
        
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
    
    def _check_and_warn_constraints(self, response: str) -> str:
        """Check if response violates program constraints"""
        return response
    
    def _get_memory_summary(self):
        """Generate a summary of important information from conversation"""
        summary_parts = []
        
        user_name = self.session_manager.session_data.get('user_name')
        if user_name:
            summary_parts.append(f"Participant name: {user_name}")
        
        # Add discovery information if available
        discovery = self.session_manager.session_data.get('discovery', {})
        if discovery:
            discovery_items = []
            if discovery.get('general_about'):
                discovery_items.append(f"  - Background: {discovery['general_about']}")
            if discovery.get('current_exercise'):
                discovery_items.append(f"  - Current exercise: {discovery['current_exercise']}")
            if discovery.get('current_sleep'):
                discovery_items.append(f"  - Sleep habits: {discovery['current_sleep']}")
            if discovery.get('current_eating'):
                discovery_items.append(f"  - Eating habits: {discovery['current_eating']}")
            if discovery.get('free_time_activities'):
                discovery_items.append(f"  - Free time activities: {discovery['free_time_activities']}")
            
            if discovery_items:
                summary_parts.append("\nDiscovery information:")
                summary_parts.extend(discovery_items)
        
        # Add all goals with details
        goal_details = self.session_manager.session_data.get('goal_details', [])
        if goal_details:
            summary_parts.append(f"\nGoals set ({len(goal_details)} total):")
            for i, goal_info in enumerate(goal_details, 1):
                goal_text = goal_info['goal']
                confidence = goal_info.get('confidence', 'N/A')
                summary_parts.append(f"  {i}. {goal_text} (Confidence: {confidence}/10)")
        
        # Also include current goal being worked on (if not yet stored)
        current_goal = self.session_manager.session_data.get('current_goal')
        if current_goal and not any(g['goal'] == current_goal for g in goal_details):
            summary_parts.append(f"\nCurrent goal being refined: {current_goal}")
        
        return "\n".join(summary_parts) if summary_parts else ""
    
    def get_session_info(self):
        """Get current session state and data"""
        return {
            "state": self.session_manager.get_state().value,
            "data": self.session_manager.get_session_summary(),
            "total_messages": len(self.conversation_history),
            "memory_summary": self._get_memory_summary()
        }
    
    def save_session(self, filename=None):
        """Save current session including conversation history"""
        return self.session_manager.save_session(filename, self.conversation_history)
    
    def load_session(self, filename):
        """Load session including conversation history"""
        history = self.session_manager.load_session(filename)
        self.conversation_history = history
        return history
    
    def reset_session(self):
        """Reset session to beginning"""
        self.session_manager = Session1Manager(self.program_info_file)
        self.session_manager.set_llm_client(self._create_llm_evaluator())
        self.conversation_history = []
        print("✓ Session reset to beginning")


def interactive_session_chat():
    """Interactive chat with session management"""
    print("=" * 80)
    print("Health Coaching Session 1 - Structured Flow")
    print("=" * 80)
    
    print("\nCommands:")
    print("  'status' - Show current session state and data")
    print("  'save' - Save current session to file")
    print("  'reset' - Start session over from beginning")
    print("  'quit' - Exit")
    print("\n" + "=" * 80 + "\n")
    
    chatbot = SessionBasedRAGChatbot(model='claude-sonnet-4.5')
    
    print("Nala: ", end="")
    initial_response, _, _ = chatbot.generate_response("[START_SESSION]")
    print("\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            save = input("\nWould you like to save this session? (yes/no): ").strip().lower()
            if save in ['yes', 'y']:
                filename = chatbot.save_session()
                print(f"✓ Session saved to {filename}")
            print("\nThanks for participating in your coaching session!")
            break
        
        if user_input.lower() == 'status':
            info = chatbot.get_session_info()
            print(f"\n--- Session Status ---")
            print(f"Current State: {info['state']}")
            print(f"Turn Count: {info['data']['duration_turns']}")
            print(f"Total Messages: {info['total_messages']}")
            print(f"User Name: {info['data']['session_data'].get('user_name', 'Not set')}")
            
            discovery = info['data']['session_data'].get('discovery', {})
            questions_asked = discovery.get('questions_asked', [])
            if questions_asked:
                print(f"\nDiscovery Questions Asked: {len(questions_asked)}")
                print(f"Topics covered: {', '.join(questions_asked)}")
            
            goal_details = info['data']['session_data'].get('goal_details', [])
            if goal_details:
                print(f"\nGoals ({len(goal_details)} total):")
                for i, goal_info in enumerate(goal_details, 1):
                    print(f"  {i}. {goal_info['goal']}")
                    print(f"     Confidence: {goal_info['confidence']}/10")
            else:
                print(f"Goals: No completed goals yet")
            
            current_goal = info['data']['session_data'].get('current_goal')
            if current_goal:
                print(f"\nCurrent goal in progress: {current_goal}")
            
            if info['memory_summary']:
                print(f"\nMemory Summary:\n{info['memory_summary']}")
            print()
            continue
        
        if user_input.lower() == 'save':
            filename = chatbot.save_session()
            print(f"✓ Session saved to {filename}\n")
            continue
        
        if user_input.lower() == 'reset':
            confirm = input("Are you sure you want to restart the session? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                chatbot.reset_session()
                print("\nNala: Let's start fresh...\n")
                initial_response, _, _ = chatbot.generate_response("Hello")
                print("\n")
            continue
        
        try:
            print("\nNala: ", end="")
            response, sources, model_name = chatbot.generate_response(user_input)
            print("\n")
            
            session_state = chatbot.session_manager.get_state()
            if session_state == SessionState.END_SESSION:
                print("\n" + "=" * 80)
                print("SESSION 1 COMPLETE!")
                print("=" * 80)
                
                filename = chatbot.save_session()
                print(f"\n✓ Session automatically saved to: {filename}")
                
                info = chatbot.get_session_info()
                goal_details = info['data']['session_data'].get('goal_details', [])
                if goal_details:
                    print(f"\n📊 Session Summary:")
                    print(f"   Participant: {info['data']['session_data'].get('user_name', 'N/A')}")
                    print(f"   Goals Set: {len(goal_details)}")
                    for i, goal_info in enumerate(goal_details, 1):
                        print(f"   {i}. {goal_info['goal']}")
                        print(f"      Confidence: {goal_info['confidence']}/10")
                
                print(f"\n👋 See you next week at Session 2!")
                print("=" * 80 + "\n")
                break
            
        except Exception as e:
            print(f"\nError: {e}\n")
    
    final_save = input("\nSave final session? (yes/no): ").strip().lower()
    if final_save in ['yes', 'y']:
        filename = chatbot.save_session()
        print(f"✓ Final session saved to {filename}")


if __name__ == "__main__":
    interactive_session_chat()