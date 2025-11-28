"""
Session 4 RAG Chatbot - Final Session (Long-term Goal Sustainability)
Inherits common functionality from BaseSessionRAGChatbot.
"""
from base_session_chatbot import BaseSessionRAGChatbot
from session4 import Session4Manager, Session4State
import os
from dotenv import load_dotenv
import json

from utils.database import load_session_from_db, list_users, get_user_by_name

load_dotenv()


class Session4RAGChatbot(BaseSessionRAGChatbot):
    """
    Session 4 chatbot for final check-in and long-term planning.
    Inherits common functionality from BaseSessionRAGChatbot.
    """
    
    def __init__(self, session3_data=None, model='claude-sonnet-4.5', top_k=3, 
                 recent_messages=6, relevant_history_count=4, validate_constraints=True):
        # Initialize base class
        super().__init__(
            model=model,
            top_k=top_k,
            recent_messages=recent_messages,
            relevant_history_count=relevant_history_count,
            validate_constraints=validate_constraints
        )
        
        # Session 4 specific setup
        self.session_manager = Session4Manager(user_profile=session3_data)
        self.session_manager.set_llm_client(self._create_llm_evaluator())
    
    def _get_memory_summary(self):
        """Generate Session 4 specific memory summary"""
        summary_parts = []
        
        # User name
        user_name = self.session_manager.session_data.get('user_name')
        if user_name:
            summary_parts.append(f"Participant name: {user_name}")
        
        # Previous goals
        previous_goals = self.session_manager.session_data.get('previous_goals', [])
        if previous_goals:
            summary_parts.append(f"\nGoals from previous session ({len(previous_goals)} total):")
            for i, goal_info in enumerate(previous_goals, 1):
                goal_text = goal_info['goal']
                confidence = goal_info.get('confidence', 'N/A')
                summary_parts.append(f"  {i}. {goal_text} (Confidence: {confidence}/10)")
        
        # Goals achievement status
        goals_achieved = self.session_manager.session_data.get('goals_achieved')
        if goals_achieved is not None:
            status = "Goals were achieved" if goals_achieved else "Goals were not fully achieved"
            summary_parts.append(f"\n{status}")
        
        # Stress level
        stress_level = self.session_manager.session_data.get('stress_level')
        if stress_level:
            summary_parts.append(f"Stress level: {stress_level}/10")
        
        # What happened
        what_happened = self.session_manager.session_data.get('what_happened')
        if what_happened:
            summary_parts.append(f"\nWhat happened: {what_happened[:100]}...")
        
        # Path chosen
        path_chosen = self.session_manager.session_data.get('path_chosen')
        if path_chosen:
            path_names = {
                'current': 'Focusing on current goals',
                'new': 'Setting new goals'
            }
            summary_parts.append(f"\nPath chosen: {path_names.get(path_chosen, path_chosen)}")
        
        # New goals for this session
        new_goals = self.session_manager.session_data.get('new_goals', [])
        if new_goals:
            summary_parts.append(f"\nNew goals set this session ({len(new_goals)} total):")
            for i, goal in enumerate(new_goals, 1):
                summary_parts.append(f"  {i}. {goal}")
        
        # Confidence level
        confidence = self.session_manager.session_data.get('confidence_level')
        if confidence:
            summary_parts.append(f"\nConfidence level: {confidence}/10")
        
        # Tracking method
        tracking = self.session_manager.session_data.get('tracking_method')
        if tracking:
            summary_parts.append(f"\nTracking method: {tracking}")
        
        # Continuation plan
        continuation = self.session_manager.session_data.get('continuation_plan')
        if continuation:
            summary_parts.append(f"\nLong-term plan: {continuation[:100]}...")
        
        return "\n".join(summary_parts) if summary_parts else ""
    
    def get_session_info(self):
        """Get current session state and data (Session 4 format)"""
        return {
            "session_number": 4,
            "state": self.session_manager.get_state().value,
            "data": self.session_manager.get_session_summary(),
            "total_messages": len(self.conversation_history),
            "memory_summary": self._get_memory_summary()
        }
    
    def reset_session(self):
        """Reset Session 4 to beginning"""
        user_profile = {
            "goals": self.session_manager.session_data.get('previous_goals'),
            "uid": self.session_manager.uid,
            "name": self.session_manager.session_data.get('user_name')
        }
        self.session_manager = Session4Manager(user_profile=user_profile)
        self.session_manager.set_llm_client(self._create_llm_evaluator())
        self.conversation_history = []
        print("✓ Session 4 reset to beginning")
    
    def load_and_inject_history(self, filename: str = None, uid: str = None):
        """
        Load session from database/file and inject chat history into conversation
        
        Args:
            filename: Path to JSON file (optional)
            uid: User ID for database lookup (optional)
        
        Returns:
            bool: True if history was loaded and injected successfully
        """
        # Load session data and get chat history
        chat_history = self.session_manager.load_session(filename=filename, uid=uid, inject_history=True)
        
        if chat_history:
            # Inject into conversation history
            self.conversation_history = chat_history
            print(f"✓ Loaded and injected {len(chat_history)} messages into conversation history")
            return True
        else:
            print("ℹ No chat history found to inject")
            return False


def interactive_session4_chat():
    """Interactive chat for Session 4"""
    print("=" * 80)
    print("Health Coaching Session 4 - Final Check-in & Long-term Planning")
    print("=" * 80)
    
    print("\nHow would you like to load Session 3 data?")
    print("  1. From database (select user)")
    print("  2. From JSON file")
    print("  3. Start fresh (no previous data)")
    
    load_choice = input("Choose (1/2/3): ").strip()
    
    session3_data = None
    
    if load_choice == '1':
        users = list_users()
        if users:
            print("\nAvailable users:")
            for i, user in enumerate(users, 1):
                name = user.get('name') or 'Unknown'
                print(f"  {i}. {name} (UID: {user['uid']}, Session {user['last_session']})")
            
            print(f"\n  Or enter a name to search")
            user_choice = input("\nSelect number or enter name: ").strip()
            
            uid = None
            if user_choice.isdigit() and 1 <= int(user_choice) <= len(users):
                uid = users[int(user_choice) - 1]['uid']
            else:
                # Search by name
                found = get_user_by_name(user_choice)
                if found:
                    uid = found['uid']
                    print(f"Found user: {found['user_profile'].get('name')}")
                else:
                    print(f"No user found with name '{user_choice}'")
            
            if uid:
                db_data = load_session_from_db(uid, 3)
                if db_data:
                    session3_data = db_data['user_profile']
                    print(f"\n✓ Loaded Session 3 data from database")
                    
                    if session3_data.get('name'):
                        print(f"  Participant: {session3_data['name']}")
                    if session3_data.get('goals'):
                        active_goals = [g for g in session3_data['goals'] if g.get('status') == 'active']
                        print(f"  Active goals: {len(active_goals)} goal(s)")
                        for i, goal_info in enumerate(active_goals, 1):
                            if isinstance(goal_info, dict):
                                print(f"    {i}. {goal_info.get('goal')}")
                            else:
                                print(f"    {i}. {goal_info}")
                else:
                    print(f"No Session 3 data found for UID: {uid}")
        else:
            print("No users found in database.")
    
    elif load_choice == '2':
        # Existing JSON file loading...
        session3_file = input("Enter Session 3 filename: ").strip()
        if os.path.exists(session3_file):
            try:
                with open(session3_file, 'r') as f:
                    session3_full_data = json.load(f)
                
                if 'user_profile' in session3_full_data:
                    session3_data = session3_full_data['user_profile']
                else:
                    raw_data = session3_full_data.get('session_data', {})
                    session3_data = {
                        "uid": raw_data.get("uid"),
                        "name": raw_data.get("user_name"),
                        "goals": raw_data.get("goal_details", []),
                        "discovery_questions": raw_data.get("discovery", {})
                    }
                print(f"✓ Loaded from file")
            except Exception as e:
                print(f"Error loading file: {e}")
    
    print("\n" + "=" * 80)
    print("Commands:")
    print("  'status' - Show current session state and data")
    print("  'save' - Save current session to file")
    print("  'reset' - Start session over from beginning")
    print("  'quit' - Exit")
    print("=" * 80 + "\n")
    
    chatbot = Session4RAGChatbot(
        session3_data=session3_data,
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
            print("\nThanks for participating in your coaching sessions! Best of luck with your goals!")
            break
        
        if user_input.lower() == 'status':
            info = chatbot.get_session_info()
            print(f"\n--- Session 4 Status ---")
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
            if session_state == Session4State.END_SESSION:
                print("\n" + "=" * 80)
                print("SESSION 4 COMPLETE - ALL SESSIONS FINISHED!")
                print("=" * 80)
                
                filename = chatbot.save_session()
                print(f"\n✓ Final session automatically saved to: {filename}")
                
                info = chatbot.get_session_info()
                print(f"\n📊 Final Session Summary:")
                if info['memory_summary']:
                    print(info['memory_summary'])
                
                print(f"\n🎉 Congratulations on completing all 4 coaching sessions!")
                print("Remember to continue working toward your goals and apply what you've learned.")
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
    interactive_session4_chat()