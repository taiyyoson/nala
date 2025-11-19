"""
Session 2 RAG Chatbot - Refactored with Base Class
Only Session 2 specific logic remains here.
All common functionality moved to BaseSessionRAGChatbot.
"""
from base_session_chatbot import BaseSessionRAGChatbot
from session2 import Session2Manager, Session2State
import os
from dotenv import load_dotenv
import json

load_dotenv()


class Session2RAGChatbot(BaseSessionRAGChatbot):
    """
    Session 2 chatbot for progress review and goal adjustment.
    Inherits common functionality from BaseSessionRAGChatbot.
    """
    
    def __init__(self, session1_data=None, model='claude-sonnet-4.5', top_k=3, 
                 recent_messages=6, relevant_history_count=4, validate_constraints=True):
        # Initialize base class
        super().__init__(
            model=model,
            top_k=top_k,
            recent_messages=recent_messages,
            relevant_history_count=relevant_history_count,
            validate_constraints=validate_constraints
        )
        
        # Session 2 specific setup
        self.session_manager = Session2Manager(session1_data=session1_data)
        self.session_manager.set_llm_client(self._create_llm_evaluator())
    
    def _get_memory_summary(self):
        """Generate Session 2 specific memory summary"""
        summary_parts = []
        
        # User name
        user_name = self.session_manager.session_data.get('user_name')
        if user_name:
            summary_parts.append(f"Participant name: {user_name}")
        
        # Previous goals from Session 1
        previous_goals = self.session_manager.session_data.get('previous_goals', [])
        if previous_goals:
            summary_parts.append(f"\nPrevious goals from Session 1 ({len(previous_goals)} total):")
            for i, goal_info in enumerate(previous_goals, 1):
                goal_text = goal_info['goal']
                confidence = goal_info.get('confidence', 'N/A')
                summary_parts.append(f"  {i}. {goal_text} (Confidence: {confidence}/10)")
        
        # Current session data
        stress_level = self.session_manager.session_data.get('stress_level')
        if stress_level:
            summary_parts.append(f"\nStress level this week: {stress_level}/10")
        
        # Path chosen
        path_chosen = self.session_manager.session_data.get('path_chosen')
        if path_chosen:
            path_names = {
                'same': 'Continuing with same goals',
                'different': 'Keeping some goals and adding new ones',
                'new': 'Setting completely new goals'
            }
            summary_parts.append(f"\nPath chosen: {path_names.get(path_chosen, path_chosen)}")
        
        # Goals to keep
        goals_to_keep = self.session_manager.session_data.get('goals_to_keep', [])
        if goals_to_keep:
            summary_parts.append(f"\nGoals being kept from last week:")
            for i, goal in enumerate(goals_to_keep, 1):
                summary_parts.append(f"  {i}. {goal}")
        
        # New goals for this week
        new_goals = self.session_manager.session_data.get('new_goals', [])
        if new_goals:
            summary_parts.append(f"\nNew goals for this week ({len(new_goals)} total):")
            for i, goal in enumerate(new_goals, 1):
                summary_parts.append(f"  {i}. {goal}")
        
        # Current goal being worked on
        current_goal = self.session_manager.session_data.get('current_goal')
        if current_goal and current_goal not in new_goals:
            summary_parts.append(f"\nCurrent goal being refined: {current_goal}")
        
        # Successes and challenges
        successes = self.session_manager.session_data.get('successes', [])
        if successes:
            summary_parts.append(f"\nSuccesses this week:")
            for success in successes:
                summary_parts.append(f"  - {success}")
        
        challenges = self.session_manager.session_data.get('challenges', [])
        if challenges:
            summary_parts.append(f"\nChallenges this week:")
            for challenge in challenges:
                summary_parts.append(f"  - {challenge}")
        
        return "\n".join(summary_parts) if summary_parts else ""
    
    def get_session_info(self):
        """Get current session state and data (Session 2 format)"""
        return {
            "session_number": 2,
            "state": self.session_manager.get_state().value,
            "data": self.session_manager.get_session_summary(),
            "total_messages": len(self.conversation_history),
            "memory_summary": self._get_memory_summary()
        }
    
    def reset_session(self):
        """Reset Session 2 to beginning"""
        session1_data = self.session_manager.session_data.get('previous_goals')
        self.session_manager = Session2Manager(
            session1_data={'goal_details': session1_data} if session1_data else None
        )
        self.session_manager.set_llm_client(self._create_llm_evaluator())
        self.conversation_history = []
        print("✓ Session 2 reset to beginning")


def interactive_session2_chat():
    """Interactive chat for Session 2"""
    print("=" * 80)
    print("Health Coaching Session 2 - Progress Review & Goal Adjustment")
    print("=" * 80)
    
    # Check if user wants to load Session 1 data
    print("\nWould you like to load data from Session 1?")
    load_choice = input("Load Session 1 data? (yes/no): ").strip().lower()
    
    session1_data = None
    if load_choice in ['yes', 'y']:
        session1_file = input("Enter Session 1 filename (e.g., session1_20240101_120000.json): ").strip()
        if os.path.exists(session1_file):
            try:
                with open(session1_file, 'r') as f:
                    session1_full_data = json.load(f)
                    session1_data = session1_full_data.get('session_data', {})
                print(f"✓ Loaded Session 1 data from {session1_file}")
                
                # Show what was loaded
                if session1_data.get('user_name'):
                    print(f"  Participant: {session1_data['user_name']}")
                if session1_data.get('goal_details'):
                    print(f"  Previous goals: {len(session1_data['goal_details'])} goal(s)")
                    for i, goal_info in enumerate(session1_data['goal_details'], 1):
                        print(f"    {i}. {goal_info['goal']}")
            except Exception as e:
                print(f"Error loading file: {e}")
                print("Starting Session 2 without previous data...")
        else:
            print(f"File not found: {session1_file}")
            print("Starting Session 2 without previous data...")
    
    print("\n" + "=" * 80)
    print("Commands:")
    print("  'status' - Show current session state and data")
    print("  'save' - Save current session to file")
    print("  'reset' - Start session over from beginning")
    print("  'quit' - Exit")
    print("=" * 80 + "\n")
    
    chatbot = Session2RAGChatbot(
        session1_data=session1_data,
        model='claude-sonnet-4.5'
    )
    
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
            print(f"\n--- Session 2 Status ---")
            print(f"Current State: {info['state']}")
            print(f"Turn Count: {info['data']['duration_turns']}")
            print(f"Total Messages: {info['total_messages']}")
            
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
                initial_response, _, _ = chatbot.generate_response("[START_SESSION]")
                print("\n")
            continue
        
        try:
            print("\nNala: ", end="")
            response, sources, model_name = chatbot.generate_response(user_input)
            print("\n")
            
            session_state = chatbot.session_manager.get_state()
            if session_state == Session2State.END_SESSION:
                print("\n" + "=" * 80)
                print("SESSION 2 COMPLETE!")
                print("=" * 80)
                
                filename = chatbot.save_session()
                print(f"\n✓ Session automatically saved to: {filename}")
                
                info = chatbot.get_session_info()
                print(f"\n📊 Session Summary:")
                if info['memory_summary']:
                    print(info['memory_summary'])
                
                print(f"\n👋 See you next week at Session 3!")
                print("=" * 80 + "\n")
                break
            
        except Exception as e:
            print(f"\nError: {e}\n")
            import traceback
            traceback.print_exc()
    
    final_save = input("\nSave final session? (yes/no): ").strip().lower()
    if final_save in ['yes', 'y']:
        filename = chatbot.save_session()
        print(f"✓ Final session saved to {filename}")


if __name__ == "__main__":
    interactive_session2_chat()