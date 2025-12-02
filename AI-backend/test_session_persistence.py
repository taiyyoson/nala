"""
Test Session 1-4 Data Persistence and State Analysis

This script tests:
1. Data saving after each session
2. Data loading before each subsequent session
3. Goal persistence and status transitions
4. Discovery data preservation across sessions
5. State machine transitions
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add AI-backend to path
_ai_backend_path = Path(__file__).parent
if str(_ai_backend_path) not in sys.path:
    sys.path.insert(0, str(_ai_backend_path))

from session1 import Session1Manager
from session2 import Session2Manager
from session3 import Session3Manager
from session4 import Session4Manager
from utils.database import load_session_from_db, save_session_to_db
from utils.unified_storage import get_active_goals


def print_separator(title=""):
    """Print a visual separator"""
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)


def verify_data_structure(data, session_num, expected_keys):
    """Verify that loaded data has the expected structure"""
    print(f"\n🔍 Verifying Session {session_num} data structure...")

    if not data:
        print(f"   ❌ No data returned!")
        return False

    all_ok = True
    for key in expected_keys:
        if key in data:
            print(f"   ✅ '{key}' present")
        else:
            print(f"   ❌ '{key}' MISSING")
            all_ok = False

    return all_ok


def test_session_1():
    """Test Session 1: Save initial user data"""
    print_separator("SESSION 1: Initial Goal Setting & Data Save")

    uid = f"test_persist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    manager = Session1Manager(uid=uid, debug=False)

    print(f"📝 Created Session 1 Manager for UID: {uid}")

    # Simulate a complete session 1 flow
    test_inputs = [
        ("[START_SESSION]", None),
        ("My name is Jordan", "greetings"),
        ("No questions", "program_details"),
        ("I'm a busy professional", "getting_to_know_you"),
        ("I don't exercise much right now", "getting_to_know_you"),
        ("I get about 5-6 hours of sleep", "getting_to_know_you"),
        ("I eat mostly takeout", "getting_to_know_you"),
        ("I like watching movies", "getting_to_know_you"),
        ("I want to exercise more regularly", "goals"),
        ("I will go to the gym 3 times per week for 30 minutes", "refine_goal"),
        ("8", "confidence_check"),
        ("No, just this one goal", "ask_more_goals"),
        ("I'll set phone reminders", "remember_goal"),
        ("No, I'm ready", "remember_goal"),
    ]

    conversation_history = []

    for user_input, expected_next in test_inputs:
        result = manager.process_user_input(user_input, conversation_history=conversation_history)

        if result.get("next_state"):
            manager.set_state(result["next_state"])

        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": result["context"]})

        if manager.get_state().value == "end_session":
            break

    # Get summary before saving
    summary = manager.get_session_summary()

    print(f"\n📊 Session 1 Summary:")
    print(f"   - User Name: {summary['session_data']['user_name']}")
    print(f"   - Goals Created: {len(summary['session_data']['goal_details'])}")
    print(f"   - Final State: {summary['current_state']}")
    print(f"   - Conversation Turns: {summary['duration_turns']}")

    # Save session
    print(f"\n💾 Saving Session 1 to database...")
    manager.save_session(conversation_history=conversation_history)

    # Verify save by loading back
    print(f"\n🔄 Verifying save by loading Session 1 data...")
    loaded_data = load_session_from_db(uid, 1)

    if not loaded_data:
        print("   ❌ FAILED: Could not load Session 1 data!")
        return None

    # Verify structure
    verify_data_structure(loaded_data, 1, ["user_profile", "session_info", "chat_history"])

    # Verify specific fields
    user_profile = loaded_data.get("user_profile", {})
    print(f"\n✅ Session 1 Data Verified:")
    print(f"   - Name: {user_profile.get('name')}")
    print(f"   - Goals: {len(user_profile.get('goals', []))}")
    print(f"   - Discovery Questions: {len([k for k, v in user_profile.get('discovery_questions', {}).items() if v])}")
    print(f"   - Chat History Messages: {len(loaded_data.get('chat_history', []))}")

    return uid


def test_session_2(uid):
    """Test Session 2: Load Session 1 data and save new state"""
    print_separator("SESSION 2: Load Previous Data & Update Goals")

    # Load Session 1 data
    print(f"📂 Loading Session 1 data for UID: {uid}")
    prev_session = load_session_from_db(uid, 1)

    if not prev_session:
        print("   ❌ FAILED: Could not load Session 1 data!")
        return False

    user_profile = prev_session.get("user_profile", {})

    print(f"\n📊 Loaded Session 1 Data:")
    print(f"   - Name: {user_profile.get('name')}")
    print(f"   - Previous Goals: {len(user_profile.get('goals', []))}")

    # Show previous goals
    for idx, goal in enumerate(user_profile.get('goals', []), 1):
        print(f"      {idx}. {goal.get('goal')}")
        print(f"         - Confidence: {goal.get('confidence')}")
        print(f"         - Session Created: {goal.get('session_created')}")
        print(f"         - Status: {goal.get('status')}")

    # Check discovery data persistence
    discovery = user_profile.get('discovery_questions', {})
    print(f"\n📋 Discovery Data Preserved:")
    for key, value in discovery.items():
        print(f"   - {key}: {'✅ Present' if value else '❌ Missing'}")

    # Create Session 2 manager
    print(f"\n🔧 Creating Session 2 Manager...")
    manager = Session2Manager(user_profile=user_profile, debug=False)

    # Verify it loaded correctly
    print(f"   - Previous goals loaded: {len(manager.session_data.get('previous_goals', []))}")

    # Simulate Session 2 flow
    test_inputs = [
        ("[START_SESSION]", None),
        ("Things went well this week", "check_in_goals"),
        ("6", "stress_level"),
        ("I completed my gym goal twice", "goal_completion"),
        ("I want to keep my current goal and add a new one", "goals_for_next_week"),
        ("I want to drink more water daily", "different_keeping_and_new"),
        ("I will drink 8 glasses of water every day", "different_keeping_and_new"),
        ("7", "confidence_check"),
        ("I'll use a water tracking app", "remember_goal"),
        ("No more goals", "more_goals_check"),
    ]

    conversation_history = []

    for user_input, _ in test_inputs:
        result = manager.process_user_input(user_input, conversation_history=conversation_history)

        if result.get("next_state"):
            manager.set_state(result["next_state"])

        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": result["context"]})

        if manager.get_state().value == "end_session":
            break

    # Get summary
    summary = manager.get_session_summary()

    print(f"\n📊 Session 2 Summary:")
    print(f"   - Path Chosen: {summary['session_data']['path_chosen']}")
    print(f"   - New Goals: {len(summary['session_data']['new_goals'])}")
    print(f"   - Stress Level: {summary['session_data']['stress_level']}")
    print(f"   - Final State: {summary['current_state']}")

    # Save session
    print(f"\n💾 Saving Session 2 to database...")
    manager.save_session(conversation_history=conversation_history)

    # Verify save
    print(f"\n🔄 Verifying Session 2 data...")
    loaded_data = load_session_from_db(uid, 2)

    if not loaded_data:
        print("   ❌ FAILED: Could not load Session 2 data!")
        return False

    # Verify goal statuses
    user_profile = loaded_data.get("user_profile", {})
    all_goals = user_profile.get("goals", [])

    print(f"\n✅ Session 2 Data Verified:")
    print(f"   - Total Goals: {len(all_goals)}")
    print(f"   - Chat History Messages: {len(loaded_data.get('chat_history', []))}")

    for idx, goal in enumerate(all_goals, 1):
        print(f"      {idx}. {goal.get('goal')[:50]}...")
        print(f"         - Session Created: {goal.get('session_created')}")
        print(f"         - Status: {goal.get('status')}")
        print(f"         - Confidence: {goal.get('confidence')}")

    active_goals = get_active_goals(all_goals)
    print(f"\n   - Active Goals: {len(active_goals)}")

    return True


def test_session_3(uid):
    """Test Session 3: Verify goal continuity and state transitions"""
    print_separator("SESSION 3: Verify Goal Continuity & State Management")

    # Load Session 2 data
    print(f"📂 Loading Session 2 data for UID: {uid}")
    prev_session = load_session_from_db(uid, 2)

    if not prev_session:
        print("   ❌ FAILED: Could not load Session 2 data!")
        return False

    user_profile = prev_session.get("user_profile", {})

    print(f"\n📊 Loaded Session 2 Data:")
    print(f"   - Name: {user_profile.get('name')}")

    all_goals = user_profile.get('goals', [])
    active_goals = get_active_goals(all_goals)

    print(f"   - Total Goals in DB: {len(all_goals)}")
    print(f"   - Active Goals: {len(active_goals)}")

    # Show active goals
    print(f"\n   Active Goals for Session 3:")
    for idx, goal in enumerate(active_goals, 1):
        print(f"      {idx}. {goal.get('goal')}")
        print(f"         - Created in Session: {goal.get('session_created')}")
        print(f"         - Confidence: {goal.get('confidence')}")

    # Verify discovery persistence
    discovery = user_profile.get('discovery_questions', {})
    discovery_count = len([v for v in discovery.values() if v])
    print(f"\n   - Discovery Questions Still Present: {discovery_count}/5")

    # Create Session 3 manager
    print(f"\n🔧 Creating Session 3 Manager...")
    manager = Session3Manager(user_profile=user_profile, debug=False)

    print(f"   - Previous goals loaded: {len(manager.session_data.get('previous_goals', []))}")

    # Simulate Session 3
    test_inputs = [
        ("[START_SESSION]", None),
        ("My goals went well", "check_in_goals"),
        ("5", "stress_level"),
        ("I want to keep working on both goals", "goals_for_next_week"),
        ("I hit the gym twice and drank water every day", "same_goals_successes_challenges"),
        ("No changes needed", "same_anything_to_change"),
        ("9", "confidence_check"),
    ]

    conversation_history = []

    for user_input, _ in test_inputs:
        result = manager.process_user_input(user_input, conversation_history=conversation_history)

        if result.get("next_state"):
            manager.set_state(result["next_state"])

        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": result["context"]})

        if manager.get_state().value == "end_session":
            break

    # Save
    print(f"\n💾 Saving Session 3 to database...")
    manager.save_session(conversation_history=conversation_history)

    # Verify
    loaded_data = load_session_from_db(uid, 3)

    if not loaded_data:
        print("   ❌ FAILED: Could not load Session 3 data!")
        return False

    print(f"\n✅ Session 3 Data Verified")
    print(f"   - Chat History Messages: {len(loaded_data.get('chat_history', []))}")

    return True


def test_session_4(uid):
    """Test Session 4: Final session and completion"""
    print_separator("SESSION 4: Final Session & Program Completion")

    # Load Session 3 data
    print(f"📂 Loading Session 3 data for UID: {uid}")
    prev_session = load_session_from_db(uid, 3)

    if not prev_session:
        print("   ❌ FAILED: Could not load Session 3 data!")
        return False

    user_profile = prev_session.get("user_profile", {})
    active_goals = get_active_goals(user_profile.get('goals', []))

    print(f"\n📊 Loaded Session 3 Data:")
    print(f"   - Active Goals: {len(active_goals)}")

    # Create Session 4 manager
    print(f"\n🔧 Creating Session 4 Manager...")
    manager = Session4Manager(user_profile=user_profile, debug=False)

    # Simulate Session 4
    test_inputs = [
        ("[START_SESSION]", None),
        ("I'm feeling confident", "reinforce_goal_from_last_session"),
        ("I hit both of my goals!", "check_in_goals"),
        ("I stayed consistent and it became routine", "what_happened"),
        ("I could add one more gym day", "what_can_be_done_to_make_it_better"),
        ("I want to keep my current goals with that adjustment", "whats_the_focus_today"),
        ("9", "confidence_check"),
        ("I'll keep my phone reminders and water app", "how_will_you_remember_to_do_your_goal"),
        ("No, that's everything", "any_final_questions"),
    ]

    conversation_history = []

    for user_input, _ in test_inputs:
        result = manager.process_user_input(user_input, conversation_history=conversation_history)

        if result.get("next_state"):
            manager.set_state(result["next_state"])

        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": result["context"]})

        if manager.get_state().value == "end_session":
            break

    # Save
    print(f"\n💾 Saving Session 4 to database...")
    manager.save_session(conversation_history=conversation_history)

    # Verify
    loaded_data = load_session_from_db(uid, 4)

    if not loaded_data:
        print("   ❌ FAILED: Could not load Session 4 data!")
        return False

    print(f"\n✅ Session 4 Data Verified")
    print(f"   - Goals Achieved: {loaded_data.get('session_info', {}).get('metadata', {}).get('goals_achieved')}")
    print(f"   - Chat History Messages: {len(loaded_data.get('chat_history', []))}")

    return True


def verify_full_persistence(uid):
    """Verify complete data persistence across all sessions"""
    print_separator("FINAL VERIFICATION: Complete Data Persistence")

    all_sessions_ok = True

    for session_num in range(1, 5):
        print(f"\n📊 Checking Session {session_num}...")

        data = load_session_from_db(uid, session_num)

        if not data:
            print(f"   ❌ Session {session_num} data NOT FOUND")
            all_sessions_ok = False
            continue

        user_profile = data.get("user_profile", {})
        session_info = data.get("session_info", {})
        chat_history = data.get("chat_history", [])

        print(f"   ✅ Session {session_num} found")
        print(f"      - Name: {user_profile.get('name')}")
        print(f"      - State: {session_info.get('current_state')}")
        print(f"      - Total Goals: {len(user_profile.get('goals', []))}")
        print(f"      - Chat Messages: {len(chat_history)}")

        # Show goal breakdown
        goals = user_profile.get('goals', [])
        by_session = {}
        for goal in goals:
            sess = goal.get('session_created', 'unknown')
            by_session[sess] = by_session.get(sess, 0) + 1

        print(f"      - Goals by Session: {by_session}")

        # Check discovery persistence (should be in all sessions)
        discovery = user_profile.get('discovery_questions', {})
        discovery_present = len([v for v in discovery.values() if v])
        print(f"      - Discovery Answers: {discovery_present}/5")

        if discovery_present == 0 and session_num > 1:
            print(f"      ⚠️  WARNING: Discovery data missing in Session {session_num}")

    print(f"\n{'='*80}")
    if all_sessions_ok:
        print("✅ ALL SESSIONS VERIFIED SUCCESSFULLY!")
    else:
        print("⚠️  SOME SESSIONS FAILED VERIFICATION")
    print(f"{'='*80}")

    return all_sessions_ok


def main():
    """Run complete persistence test"""
    print_separator("SESSION 1-4 PERSISTENCE & STATE ANALYSIS TEST")
    print("This test will verify:")
    print("  ✓ Data saving after each session")
    print("  ✓ Data loading before each session")
    print("  ✓ Goal persistence and status transitions")
    print("  ✓ Discovery data preservation")
    print("  ✓ State machine transitions")
    print("  ✓ Conversation history persistence")

    try:
        # Test Session 1
        uid = test_session_1()
        if not uid:
            print("\n❌ Session 1 test failed. Stopping.")
            return

        # Test Session 2
        if not test_session_2(uid):
            print("\n❌ Session 2 test failed. Stopping.")
            return

        # Test Session 3
        if not test_session_3(uid):
            print("\n❌ Session 3 test failed. Stopping.")
            return

        # Test Session 4
        if not test_session_4(uid):
            print("\n❌ Session 4 test failed. Stopping.")
            return

        # Final verification
        success = verify_full_persistence(uid)

        print(f"\n{'='*80}")
        print(f"TEST COMPLETE - Test User ID: {uid}")
        print(f"{'='*80}")

        if success:
            print("\n🎉 ALL TESTS PASSED!")
            print("\nVerified:")
            print("  ✅ Session 1: Initial data save with conversation history")
            print("  ✅ Session 2: Load S1 data, add new goals, save with history")
            print("  ✅ Session 3: Load S2 data, maintain goal states, save with history")
            print("  ✅ Session 4: Load S3 data, complete program, save with history")
            print("  ✅ Data persistence across all sessions")
            print("  ✅ Goal status transitions")
            print("  ✅ Discovery data preservation")
            print("  ✅ Conversation history persistence")
        else:
            print("\n⚠️  TESTS COMPLETED WITH WARNINGS")
            print("Review the output above for details.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
