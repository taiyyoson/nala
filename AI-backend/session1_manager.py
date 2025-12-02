"""
Session 1 RAG Chatbot - Refactored with Base Class
Only Session 1 specific logic remains here.
All common functionality moved to BaseSessionRAGChatbot.
"""
from base_session_chatbot import BaseSessionRAGChatbot
from session1 import Session1Manager, SessionState
import os
from dotenv import load_dotenv

load_dotenv()


class SessionBasedRAGChatbot(BaseSessionRAGChatbot):
    """
    Session 1 chatbot for initial goal setting and participant discovery.
    Inherits common functionality from BaseSessionRAGChatbot.
    """
    
    def __init__(self, model='claude-sonnet-4.5', top_k=3, program_info_file='program_info.txt',
                 recent_messages=6, relevant_history_count=4, validate_constraints=True, uid=None):
        # Initialize base class
        super().__init__(
            model=model,
            top_k=top_k,
            recent_messages=recent_messages,
            relevant_history_count=relevant_history_count,
            validate_constraints=validate_constraints
        )

        # Session 1 specific setup
        self.program_info_file = program_info_file
        self.session_manager = Session1Manager(program_info_file=program_info_file, uid=uid)
        self.session_manager.set_llm_client(self._create_llm_evaluator())
    
    def _get_memory_summary(self):
        """Generate Session 1 specific memory summary"""
        summary_parts = []
        
        # User name
        user_name = self.session_manager.session_data.get('user_name')
        if user_name:
            summary_parts.append(f"Participant name: {user_name}")
        
        # Discovery information
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
        
        # Goals
        goal_details = self.session_manager.session_data.get('goal_details', [])
        if goal_details:
            summary_parts.append(f"\nGoals set ({len(goal_details)} total):")
            for i, goal_info in enumerate(goal_details, 1):
                goal_text = goal_info['goal']
                confidence = goal_info.get('confidence', 'N/A')
                summary_parts.append(f"  {i}. {goal_text} (Confidence: {confidence}/10)")
        
        # Current goal being refined
        current_goal = self.session_manager.session_data.get('current_goal')
        if current_goal and not any(g['goal'] == current_goal for g in goal_details):
            summary_parts.append(f"\nCurrent goal being refined: {current_goal}")
        
        return "\n".join(summary_parts) if summary_parts else ""
    
    def get_status(self):
        """
        Get current session status as a structured dictionary.
        Session 1 specific format with discovery and goal tracking.
        """
        info = self.get_session_info()
        
        # Extract discovery information
        discovery = info['data']['session_data'].get('discovery', {})
        questions_asked = discovery.get('questions_asked', [])
        
        # Extract goal information
        goal_details = info['data']['session_data'].get('goal_details', [])
        current_goal = info['data']['session_data'].get('current_goal')
        
        # Build structured status dictionary
        status = {
            'current_state': info['state'],
            'turn_count': info['data']['duration_turns'],
            'total_messages': info['total_messages'],
            'user_name': info['data']['session_data'].get('user_name'),
            'discovery': {
                'questions_asked_count': len(questions_asked),
                'topics_covered': questions_asked,
                'general_about': discovery.get('general_about'),
                'current_exercise': discovery.get('current_exercise'),
                'current_sleep': discovery.get('current_sleep'),
                'current_eating': discovery.get('current_eating'),
                'free_time_activities': discovery.get('free_time_activities'),
            },
            'goals': [
                {
                    'goal': g['goal'],
                    'confidence': g.get('confidence', 'N/A')
                }
                for g in goal_details
            ],
            'goals_count': len(goal_details),
            'current_goal': current_goal,
            'memory_summary': info['memory_summary']
        }
        
        return status
    
    def get_session_info(self):
        """Get current session state and data (Session 1 format)"""
        return {
            "state": self.session_manager.get_state().value,
            "data": self.session_manager.get_session_summary(),
            "total_messages": len(self.conversation_history),
            "memory_summary": self._get_memory_summary()
        }
    
    def reset_session(self):
        """Reset Session 1 to beginning"""
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