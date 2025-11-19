"""
Session 3 RAG Chatbot - Refactored with Base Class
Only Session 3 specific logic remains here.
All common functionality moved to BaseSessionRAGChatbot.
"""
from base_session_chatbot import BaseSessionRAGChatbot
from session3 import Session3Manager, Session3State
import os
from dotenv import load_dotenv
import json

load_dotenv()


class Session3RAGChatbot(BaseSessionRAGChatbot):
    """
    Session 3 chatbot for progress review and goal adjustment.
    Inherits common functionality from BaseSessionRAGChatbot.
    """
    
    def __init__(self, session2_data=None, model='claude-sonnet-4.5', top_k=3, 
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
        self.session_manager = Session3Manager(session2_data=session2_data)
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
        """Get current session state and data (Session 3 format)"""
        return {
            "session_number": 3,
            "state": self.session_manager.get_state().value,
            "data": self.session_manager.get_session_summary(),
            "total_messages": len(self.conversation_history),
            "memory_summary": self._get_memory_summary()
        }
    
    def reset_session(self):
        """Reset Session 3 to beginning"""
        session2_data = self.session_manager.session_data.get('previous_goals')
        self.session_manager = Session3Manager(
            session2_data={'goal_details': session2_data} if session2_data else None
        )
        self.session_manager.set_llm_client(self._create_llm_evaluator())
        self.conversation_history = []
        print("✓ Session 2 reset to beginning")


def interactive_session3_chat():
    """Interactive chat for Session 3"""
    print("=" * 80)
    print("Health Coaching Session 3 - Progress Review & Goal Adjustment pt 2")
    print("=" * 80)
    
    # Check if user wants to load Session 2 data
    print("\nWould you like to load data from Session 2?")
    load_choice = input("Load Session 2 data? (yes/no): ").strip().lower()
    
    session2_data = None
    if load_choice in ['yes', 'y']:
        session2_file = input("Enter Session 2 filename (e.g., session2_20240101_120000.json): ").strip()
        if os.path.exists(session2_file):
            try:
                with open(session2_file, 'r') as f:
                    session2_full_data = json.load(f)
                    session2_data = session2_full_data.get('session_data', {})
                print(f"✓ Loaded Session 1 data from {session2_file}")
                
                # Show what was loaded
                if session2_data.get('user_name'):
                    print(f"  Participant: {session2_data['user_name']}")
                if session2_data.get('goal_details'):
                    print(f"  Previous goals: {len(session2_data['goal_details'])} goal(s)")
                    for i, goal_info in enumerate(session2_data['goal_details'], 1):
                        print(f"    {i}. {goal_info['goal']}")
            except Exception as e:
                print(f"Error loading file: {e}")
                print("Starting Session 3 without previous data...")
        else:
            print(f"File not found: {session2_file}")
            print("Starting Session 3 without previous data...")
    
    print("\n" + "=" * 80)
    print("Commands:")
    print("  'status' - Show current session state and data")
    print("  'save' - Save current session to file")
    print("  'reset' - Start session over from beginning")
    print("  'quit' - Exit")
    print("=" * 80 + "\n")
    
    chatbot = Session3RAGChatbot(
        session2_data=session2_data,
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
            print(f"\n--- Session 3 Status ---")
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
            if session_state == Session3State.END_SESSION:
                print("\n" + "=" * 80)
                print("SESSION 3 COMPLETE!")
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
    interactive_session3_chat()