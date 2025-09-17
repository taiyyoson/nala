import re
from typing import List

def clean_corpus(file_path: str) -> List[str]:
    """
    Clean health coaching corpus that contains 'Health Coach:' and 'Participant:' dialogues.
    Returns a list suitable for ChatterBot ListTrainer.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. Using minimal training data.")
        return get_fallback_health_coaching_data()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return get_fallback_health_coaching_data()
    
    # Parse the health coaching conversations
    conversations = parse_health_coaching_conversations(content)
    
    if not conversations:
        print("No valid conversations found in corpus. Using fallback data.")
        return get_fallback_health_coaching_data()
    
    return conversations

def parse_health_coaching_conversations(content: str) -> List[str]:
    """
    Parse conversations between Health Coach and Participant.
    Properly handles multiline responses that may contain role keywords within the text.
    Returns alternating list: [participant_msg, coach_response, participant_msg, coach_response, ...]
    """
    conversations = []
    
    # Split content by role markers at the beginning of lines
    # This regex looks for "Health Coach:" or "Participant:" at the start of a line or after whitespace
    role_pattern = r'(?:^|\n)\s*(Health Coach:|Participant:)\s*'
    
    # Split the content and keep the separators
    parts = re.split(role_pattern, content, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove empty parts and organize into (role, message) pairs
    sequence = []
    current_role = None
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # Check if this part is a role indicator
        if re.match(r'^Health Coach:

def clean_message(message: str) -> str:
    """Clean individual messages while preserving the health coaching tone and multiline structure"""
    if not message:
        return ""
    
    # Preserve line breaks but normalize excessive whitespace
    lines = message.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Clean each line individually
        line = line.strip()
        if line:
            # Remove any role indicators that might have been included in the middle of text
            line = re.sub(r'^(Health Coach|Participant):\s*', '', line, flags=re.IGNORECASE)
            # Normalize whitespace within the line
            line = re.sub(r'\s+', ' ', line).strip()
            if line:
                cleaned_lines.append(line)
    
    # Join lines back together
    message = '\n'.join(cleaned_lines)
    
    # Remove very short or empty messages
    if len(message.strip()) < 3:
        return ""
    
    # Remove messages that are just punctuation
    if not re.search(r'[a-zA-Z]', message):
        return ""
    
    # Ensure proper sentence capitalization for the first line
    if message and message[0].islower():
        message = message[0].upper() + message[1:]
    
    return message.strip()

def get_fallback_health_coaching_data() -> List[str]:
    """Provide fallback health coaching conversations if main corpus is unavailable"""
    return [
        # Basic greetings and goal setting
        "Hi", "Hello! I'm here to help you with your health goals. What would you like to work on today?",
        "Hello", "Hi there! Let's talk about your health and wellness. What's on your mind?",
        "I need help", "I'm here to help you. What specific area of your health or wellness would you like to focus on?",
        
        # SMART goal setting conversations
        "I want to be healthier", "That's a great goal! Can you tell me more specifically what aspect of your health you'd like to focus on?",
        "I want to eat better", "That's wonderful! Can you tell me what eating better means to you specifically?",
        "I want to exercise more", "Exercise is so important! What kind of physical activity interests you most?",
        "I want to lose weight", "Weight management can be a great goal. What specifically would you like to focus on to support that?",
        
        # Follow-up coaching questions
        "I want to eat more fruits and vegetables", "Can you tell me a little about why eating more fruits and vegetables is important to you?",
        "I want to walk every day", "That's a great goal! How many days per week are you thinking, and for how long?",
        "I want to drink more water", "Staying hydrated is so important! How much water are you drinking now?",
        
        # Motivational and clarifying responses
        "It's important for my health", "That's a strong motivation! What would success look like to you?",
        "My doctor recommended it", "It's great that you're following your doctor's advice. How do you feel about making this change?",
        "I feel better when I do it", "That's wonderful that you notice how it makes you feel! How can we help you do it more consistently?",
        
        # Support and encouragement
        "I'm not sure I can do it", "It's normal to feel uncertain about changes. What feels most challenging about this goal?",
        "I've tried before and failed", "Many people need several attempts before success. What do you think might work differently this time?",
        "I don't have time", "Time can definitely be a challenge. Let's think about what might be realistic for your schedule.",
        
        # Closing and next steps
        "Thank you", "You're so welcome! What feels like a good next step for you?",
        "This is helpful", "I'm glad this is helpful! What would you like to focus on moving forward?",
        "I think I can do this", "That confidence is wonderful! How would you like to start?",
    ]

def analyze_corpus(file_path: str) -> str:
    """Analyze the health coaching corpus to understand its structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Count role mentions
        coach_mentions = len(re.findall(r'Health Coach:', content, re.IGNORECASE))
        participant_mentions = len(re.findall(r'Participant:', content, re.IGNORECASE))
        
        # Parse conversations
        conversations = parse_health_coaching_conversations(content)
        
        # Analyze conversation characteristics
        if conversations:
            coach_responses = [conversations[i] for i in range(1, len(conversations), 2)]
            participant_inputs = [conversations[i] for i in range(0, len(conversations), 2)]
            
            avg_coach_length = sum(len(r.split()) for r in coach_responses) / len(coach_responses) if coach_responses else 0
            avg_participant_length = sum(len(p.split()) for p in participant_inputs) / len(participant_inputs) if participant_inputs else 0
            
            # Common coaching words
            coaching_words = ['goal', 'specific', 'tell me', 'why', 'important', 'how', 'what', 'can you']
            word_counts = {}
            all_coach_text = ' '.join(coach_responses).lower()
            
            for word in coaching_words:
                word_counts[word] = all_coach_text.count(word)
        
        analysis = f"""
Health Coaching Corpus Analysis:
- Health Coach mentions: {coach_mentions}
- Participant mentions: {participant_mentions}
- Training pairs extracted: {len(conversations) // 2}
- Average coach response length: {avg_coach_length:.1f} words
- Average participant input length: {avg_participant_length:.1f} words
- Common coaching words found: {word_counts}
        """
        
        return analysis.strip()
        
    except Exception as e:
        return f"Error analyzing corpus: {e}"

if __name__ == "__main__":
    # Test the cleaning function
    test_file = "health-training-data.txt"
    
    print("Analyzing health coaching corpus...")
    analysis = analyze_corpus(test_file)
    print(analysis)
    
    print("\nCleaning corpus...")
    cleaned = clean_corpus(test_file)
    print(f"Extracted {len(cleaned)} training items ({len(cleaned)//2} conversation pairs)")
    
    if cleaned:
        print("\nSample conversations:")
        for i in range(0, min(8, len(cleaned)), 2):
            if i + 1 < len(cleaned):
                print(f"Participant: {cleaned[i]}")
                print(f"Health Coach: {cleaned[i+1]}")
                print("-" * 50), part, re.IGNORECASE):
            current_role = "coach"
        elif re.match(r'^Participant:

def clean_message(message: str) -> str:
    """Clean individual messages while preserving the health coaching tone"""
    if not message:
        return ""
    
    # Remove extra whitespace and normalize
    message = re.sub(r'\s+', ' ', message).strip()
    
    # Remove any role indicators that might have been included
    message = re.sub(r'^(Health Coach|Participant):\s*', '', message, flags=re.IGNORECASE)
    
    # Remove very short or empty messages
    if len(message.strip()) < 3:
        return ""
    
    # Remove messages that are just punctuation
    if not re.search(r'[a-zA-Z]', message):
        return ""
    
    # Ensure proper sentence capitalization
    if message and message[0].islower():
        message = message[0].upper() + message[1:]
    
    return message.strip()

def get_fallback_health_coaching_data() -> List[str]:
    """Provide fallback health coaching conversations if main corpus is unavailable"""
    return [
        # Basic greetings and goal setting
        "Hi", "Hello! I'm here to help you with your health goals. What would you like to work on today?",
        "Hello", "Hi there! Let's talk about your health and wellness. What's on your mind?",
        "I need help", "I'm here to help you. What specific area of your health or wellness would you like to focus on?",
        
        # SMART goal setting conversations
        "I want to be healthier", "That's a great goal! Can you tell me more specifically what aspect of your health you'd like to focus on?",
        "I want to eat better", "That's wonderful! Can you tell me what eating better means to you specifically?",
        "I want to exercise more", "Exercise is so important! What kind of physical activity interests you most?",
        "I want to lose weight", "Weight management can be a great goal. What specifically would you like to focus on to support that?",
        
        # Follow-up coaching questions
        "I want to eat more fruits and vegetables", "Can you tell me a little about why eating more fruits and vegetables is important to you?",
        "I want to walk every day", "That's a great goal! How many days per week are you thinking, and for how long?",
        "I want to drink more water", "Staying hydrated is so important! How much water are you drinking now?",
        
        # Motivational and clarifying responses
        "It's important for my health", "That's a strong motivation! What would success look like to you?",
        "My doctor recommended it", "It's great that you're following your doctor's advice. How do you feel about making this change?",
        "I feel better when I do it", "That's wonderful that you notice how it makes you feel! How can we help you do it more consistently?",
        
        # Support and encouragement
        "I'm not sure I can do it", "It's normal to feel uncertain about changes. What feels most challenging about this goal?",
        "I've tried before and failed", "Many people need several attempts before success. What do you think might work differently this time?",
        "I don't have time", "Time can definitely be a challenge. Let's think about what might be realistic for your schedule.",
        
        # Closing and next steps
        "Thank you", "You're so welcome! What feels like a good next step for you?",
        "This is helpful", "I'm glad this is helpful! What would you like to focus on moving forward?",
        "I think I can do this", "That confidence is wonderful! How would you like to start?",
    ]

def analyze_corpus(file_path: str) -> str:
    """Analyze the health coaching corpus to understand its structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Count role mentions
        coach_mentions = len(re.findall(r'Health Coach:', content, re.IGNORECASE))
        participant_mentions = len(re.findall(r'Participant:', content, re.IGNORECASE))
        
        # Parse conversations
        conversations = parse_health_coaching_conversations(content)
        
        # Analyze conversation characteristics
        if conversations:
            coach_responses = [conversations[i] for i in range(1, len(conversations), 2)]
            participant_inputs = [conversations[i] for i in range(0, len(conversations), 2)]
            
            avg_coach_length = sum(len(r.split()) for r in coach_responses) / len(coach_responses) if coach_responses else 0
            avg_participant_length = sum(len(p.split()) for p in participant_inputs) / len(participant_inputs) if participant_inputs else 0
            
            # Common coaching words
            coaching_words = ['goal', 'specific', 'tell me', 'why', 'important', 'how', 'what', 'can you']
            word_counts = {}
            all_coach_text = ' '.join(coach_responses).lower()
            
            for word in coaching_words:
                word_counts[word] = all_coach_text.count(word)
        
        analysis = f"""
Health Coaching Corpus Analysis:
- Health Coach mentions: {coach_mentions}
- Participant mentions: {participant_mentions}
- Training pairs extracted: {len(conversations) // 2}
- Average coach response length: {avg_coach_length:.1f} words
- Average participant input length: {avg_participant_length:.1f} words
- Common coaching words found: {word_counts}
        """
        
        return analysis.strip()
        
    except Exception as e:
        return f"Error analyzing corpus: {e}"

if __name__ == "__main__":
    # Test the cleaning function
    test_file = "health-training-data.txt"
    
    print("Analyzing health coaching corpus...")
    analysis = analyze_corpus(test_file)
    print(analysis)
    
    print("\nCleaning corpus...")
    cleaned = clean_corpus(test_file)
    print(f"Extracted {len(cleaned)} training items ({len(cleaned)//2} conversation pairs)")
    
    if cleaned:
        print("\nSample conversations:")
        for i in range(0, min(8, len(cleaned)), 2):
            if i + 1 < len(cleaned):
                print(f"Participant: {cleaned[i]}")
                print(f"Health Coach: {cleaned[i+1]}")
                print("-" * 50), part, re.IGNORECASE):
            current_role = "participant"
        else:
            # This is message content
            if current_role:
                # Clean the message but preserve multiline structure
                clean_msg = clean_message(part)
                if clean_msg:
                    sequence.append((current_role, clean_msg))
                current_role = None  # Reset after adding message
    
    # Convert sequence to training pairs
    # We want: when user says something like participant, bot responds like coach
    for i in range(len(sequence) - 1):
        current_role, current_msg = sequence[i]
        next_role, next_msg = sequence[i + 1]
        
        if current_role == "participant" and next_role == "coach":
            # Participant -> Coach: User input -> Bot response
            conversations.extend([current_msg, next_msg])
    
    return conversations

def clean_message(message: str) -> str:
    """Clean individual messages while preserving the health coaching tone"""
    if not message:
        return ""
    
    # Remove extra whitespace and normalize
    message = re.sub(r'\s+', ' ', message).strip()
    
    # Remove any role indicators that might have been included
    message = re.sub(r'^(Health Coach|Participant):\s*', '', message, flags=re.IGNORECASE)
    
    # Remove very short or empty messages
    if len(message.strip()) < 3:
        return ""
    
    # Remove messages that are just punctuation
    if not re.search(r'[a-zA-Z]', message):
        return ""
    
    # Ensure proper sentence capitalization
    if message and message[0].islower():
        message = message[0].upper() + message[1:]
    
    return message.strip()

def get_fallback_health_coaching_data() -> List[str]:
    """Provide fallback health coaching conversations if main corpus is unavailable"""
    return [
        # Basic greetings and goal setting
        "Hi", "Hello! I'm here to help you with your health goals. What would you like to work on today?",
        "Hello", "Hi there! Let's talk about your health and wellness. What's on your mind?",
        "I need help", "I'm here to help you. What specific area of your health or wellness would you like to focus on?",
        
        # SMART goal setting conversations
        "I want to be healthier", "That's a great goal! Can you tell me more specifically what aspect of your health you'd like to focus on?",
        "I want to eat better", "That's wonderful! Can you tell me what eating better means to you specifically?",
        "I want to exercise more", "Exercise is so important! What kind of physical activity interests you most?",
        "I want to lose weight", "Weight management can be a great goal. What specifically would you like to focus on to support that?",
        
        # Follow-up coaching questions
        "I want to eat more fruits and vegetables", "Can you tell me a little about why eating more fruits and vegetables is important to you?",
        "I want to walk every day", "That's a great goal! How many days per week are you thinking, and for how long?",
        "I want to drink more water", "Staying hydrated is so important! How much water are you drinking now?",
        
        # Motivational and clarifying responses
        "It's important for my health", "That's a strong motivation! What would success look like to you?",
        "My doctor recommended it", "It's great that you're following your doctor's advice. How do you feel about making this change?",
        "I feel better when I do it", "That's wonderful that you notice how it makes you feel! How can we help you do it more consistently?",
        
        # Support and encouragement
        "I'm not sure I can do it", "It's normal to feel uncertain about changes. What feels most challenging about this goal?",
        "I've tried before and failed", "Many people need several attempts before success. What do you think might work differently this time?",
        "I don't have time", "Time can definitely be a challenge. Let's think about what might be realistic for your schedule.",
        
        # Closing and next steps
        "Thank you", "You're so welcome! What feels like a good next step for you?",
        "This is helpful", "I'm glad this is helpful! What would you like to focus on moving forward?",
        "I think I can do this", "That confidence is wonderful! How would you like to start?",
    ]

def analyze_corpus(file_path: str) -> str:
    """Analyze the health coaching corpus to understand its structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Count role mentions
        coach_mentions = len(re.findall(r'Health Coach:', content, re.IGNORECASE))
        participant_mentions = len(re.findall(r'Participant:', content, re.IGNORECASE))
        
        # Parse conversations
        conversations = parse_health_coaching_conversations(content)
        
        # Analyze conversation characteristics
        if conversations:
            coach_responses = [conversations[i] for i in range(1, len(conversations), 2)]
            participant_inputs = [conversations[i] for i in range(0, len(conversations), 2)]
            
            avg_coach_length = sum(len(r.split()) for r in coach_responses) / len(coach_responses) if coach_responses else 0
            avg_participant_length = sum(len(p.split()) for p in participant_inputs) / len(participant_inputs) if participant_inputs else 0
            
            # Common coaching words
            coaching_words = ['goal', 'specific', 'tell me', 'why', 'important', 'how', 'what', 'can you']
            word_counts = {}
            all_coach_text = ' '.join(coach_responses).lower()
            
            for word in coaching_words:
                word_counts[word] = all_coach_text.count(word)
        
        analysis = f"""
Health Coaching Corpus Analysis:
- Health Coach mentions: {coach_mentions}
- Participant mentions: {participant_mentions}
- Training pairs extracted: {len(conversations) // 2}
- Average coach response length: {avg_coach_length:.1f} words
- Average participant input length: {avg_participant_length:.1f} words
- Common coaching words found: {word_counts}
        """
        
        return analysis.strip()
        
    except Exception as e:
        return f"Error analyzing corpus: {e}"

if __name__ == "__main__":
    # Test the cleaning function
    test_file = "health-training-data.txt"
    
    print("Analyzing health coaching corpus...")
    analysis = analyze_corpus(test_file)
    print(analysis)
    
    print("\nCleaning corpus...")
    cleaned = clean_corpus(test_file)
    print(f"Extracted {len(cleaned)} training items ({len(cleaned)//2} conversation pairs)")
    
    if cleaned:
        print("\nSample conversations:")
        for i in range(0, min(8, len(cleaned)), 2):
            if i + 1 < len(cleaned):
                print(f"Participant: {cleaned[i]}")
                print(f"Health Coach: {cleaned[i+1]}")
                print("-" * 50)