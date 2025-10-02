import re
import csv
from pathlib import Path

def parse_plain_text_transcript(transcript_text):
    """
    Parse transcript in plain text format:
    17:57:47 Coach: Hello. How are you today.
    17:57:52 Participant: busy
    """
    lines = transcript_text.strip().split('\n')
    conversations = []
    
    current_participant = None
    current_coach = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Match format: timestamp Speaker: text
        match = re.match(r'(\d{2}:\d{2}:\d{2})\s+(Coach|Participant):\s*(.*)', line)
        if match:
            timestamp, speaker, text = match.groups()
            
            if speaker == 'Participant':
                # If we have a previous complete pair, save it
                if current_participant and current_coach:
                    conversations.append({
                        'participant_response': current_participant.strip(),
                        'coach_response': current_coach.strip(),
                        'timestamp': timestamp
                    })
                
                # Start new participant response
                current_participant = text
                current_coach = None
                
            elif speaker == 'Coach':
                if current_participant:
                    # We have a participant response, now add coach response
                    current_coach = text
                    
                    # Save the complete pair
                    conversations.append({
                        'participant_response': current_participant.strip(),
                        'coach_response': current_coach.strip(),
                        'timestamp': timestamp
                    })
                    
                    # Reset for next pair
                    current_participant = None
                    current_coach = None
    
    return conversations

def categorize_response(participant_text, coach_text):
    """
    Categorize the response based on content
    """
    participant_lower = participant_text.lower()
    coach_lower = coach_text.lower()
    
    # Determine goal type
    goal_type = 'general'
    if any(word in participant_lower + coach_lower for word in ['eat', 'food', 'takeout', 'nutrition', 'vegetables', 'meal', 'oatmeal']):
        goal_type = 'nutrition'
    elif any(word in participant_lower + coach_lower for word in ['exercise', 'walk', 'workout', 'physical', 'dog']):
        goal_type = 'exercise'
    elif any(word in participant_lower + coach_lower for word in ['stress', 'meditation', 'anxious', 'overwhelmed', 'busy']):
        goal_type = 'stress_management'
    
    # Determine context with expanded categories
    context = 'general'
    if any(phrase in coach_lower for phrase in ['scale of', 'rate yourself', 'confident']):
        context = 'confidence_assessment'
    elif any(phrase in coach_lower for phrase in ['goal', 'thinking about', 'plan']):
        context = 'goal_setting'
    elif any(phrase in coach_lower for phrase in ['barrier', 'challenge', 'difficult', 'help']):
        context = 'barrier_identification'
    elif any(phrase in coach_lower for phrase in ['how was', 'progress', 'worked out', 'week']):
        context = 'progress_review'
    elif any(phrase in coach_lower for phrase in ['hello', 'how are you']):
        context = 'greeting'
    elif any(phrase in coach_lower for phrase in ['ready', 'prepared', 'change', 'stage', 'willing']):
        context = 'coach_assessing_state_of_change'
    elif any(phrase in coach_lower for phrase in ['agenda', 'today', 'focus on', 'discuss', 'check in about']):
        context = 'establishing_agenda'
    elif any(phrase in coach_lower for phrase in ['confidence', 'confident', 'able to do', 'reach your goal']):
        context = 'confidence_to_reach_goals'
    elif any(phrase in coach_lower for phrase in ['stress', 'stressed', 'overwhelmed', 'feeling', 'level']):
        context = 'measuring_stress_level'
    elif any(phrase in coach_lower for phrase in ['support', 'help', 'need', 'assistance', 'resources']):
        context = 'support_needed_for_goals'
    
    # Estimate confidence level
    confidence = 7  # default
    if any(word in participant_lower for word in ['confident', 'easy', 'easily']):
        confidence = 8
    elif any(word in participant_lower for word in ['hard', 'difficult', 'challenging', 'nervous']):
        confidence = 5
    elif 'eight' in participant_lower or '8' in participant_lower:
        confidence = 8
    elif 'six' in participant_lower or '6' in participant_lower:
        confidence = 6
    elif 'seven' in participant_lower or '7' in participant_lower:
        confidence = 7
    
    return goal_type, context, confidence

def extract_keywords(text):
    """
    Extract meaningful keywords from text
    """
    stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 
                'is', 'are', 'was', 'were', 'i', 'you', 'we', 'they', 'it', 'that', 'this', 'so', 'like',
                'yeah', 'um', 'well', 'now', 'just', 'really', 'know', 'think', 'get', 'go', 'do', 'have'}
    
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [word for word in words if word not in stopwords and len(word) > 2]
    
    return ' '.join(keywords[:8])  # Top 8 keywords

def process_single_file(file_path):
    """
    Process one transcript file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        conversations = parse_plain_text_transcript(content)
        
        # Add metadata to each conversation
        for conv in conversations:
            goal_type, context, confidence = categorize_response(
                conv['participant_response'], 
                conv['coach_response']
            )
            
            conv['goal_type'] = goal_type
            conv['context_category'] = context
            conv['confidence_level'] = confidence
            conv['keywords'] = extract_keywords(conv['participant_response'])
            conv['source_file'] = file_path.name
        
        return conversations
    
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        return []

def process_all_files(folder_path='.'):
    """
    Process all transcript files and create CSV
    """
    folder = Path(folder_path)
    
    # Find all text files
    transcript_files = list(folder.glob('*.txt'))
    
    print(f"Found {len(transcript_files)} transcript files")
    print(f"Looking in folder: {folder.absolute()}")
    
    # Debug: show all files in directory
    all_files = list(folder.iterdir())
    print(f"All files in directory: {[f.name for f in all_files if f.is_file()]}")
    
    if not transcript_files:
        print("No .txt files found! Checking current directory...")
        current_dir = Path('.')
        txt_files = list(current_dir.glob('*.txt'))
        print(f"TXT files in current directory: {[f.name for f in txt_files]}")
        return
    
    all_conversations = []
    
    for file_path in transcript_files:
        print(f"Processing: {file_path.name}")
        conversations = process_single_file(file_path)
        all_conversations.extend(conversations)
        print(f"  - Extracted {len(conversations)} conversation pairs")
    
    if not all_conversations:
        print("No conversation pairs extracted!")
        return
    
    # Create CSV in root folder (not in transcripts folder)
    output_file = Path('.') / 'coach_responses.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['participant_response', 'coach_response', 'context_category', 
                     'goal_type', 'confidence_level', 'keywords', 'source_file']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for conv in all_conversations:
            writer.writerow({
                'participant_response': conv['participant_response'],
                'coach_response': conv['coach_response'],
                'context_category': conv['context_category'],
                'goal_type': conv['goal_type'],
                'confidence_level': conv['confidence_level'],
                'keywords': conv['keywords'],
                'source_file': conv['source_file']
            })
    
    print(f"\n✅ Successfully created {output_file}")
    print(f"Total conversation pairs: {len(all_conversations)}")
    
    # Show stats
    goal_counts = {}
    context_counts = {}
    
    for conv in all_conversations:
        goal_type = conv['goal_type']
        context = conv['context_category']
        
        goal_counts[goal_type] = goal_counts.get(goal_type, 0) + 1
        context_counts[context] = context_counts.get(context, 0) + 1
    
    print(f"\nGoal types: {goal_counts}")
    print(f"Context categories: {context_counts}")

if __name__ == "__main__":
    process_all_files("transcripts")