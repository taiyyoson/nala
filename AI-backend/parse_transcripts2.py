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
    combined_text = participant_lower + ' ' + coach_lower
    goal_type = 'general'
    
    # Nutrition / Healthy Eating
    if any(word in combined_text for word in ['fruits', 'vegetables', 'servings', 'oatmeal', 'smoothies', 'spinach', 
                                                'lasagna', 'curry', 'beans', 'rice', 'balanced meals', 'home-cooked', 
                                                'meal prep', 'grocery shopping', 'recipes', 'portion control', 
                                                'moderation', 'sugary drinks', 'healthy swaps', 'breakfast', 'lunch', 
                                                'dinner', 'mindful eating', 'variety', 'myplate', 'seasonal fruit',
                                                'eat', 'food', 'nutrition', 'meal', 'diversify meals', 'eat healthier',
                                                'turkey', 'chicken', 'clean eating', 'cheat days', 'meal variety',
                                                'healthy options', 'cook one meal', 'reduce processed foods',
                                                'intention vs action', 'food waste', 'eggs', 'cereal', 'toaster waffles',
                                                'pre-made salads', 'nutritionist', 'vitamins', 'nutrients', 'healthy eating',
                                                'my fitness pal', 'fast food', 'leftover', 'protein', 'tortillas',
                                                'broccoli', 'cucumber', 'shrimp', 'snack', 'vegetarian', 'diet',
                                                'strawberries', 'orange', 'carrots', 'fresh', 'cooking', 'gelato',
                                                'boba', 'tea', 'coffee', 'hot-cocoa', 'sandwich']):
        goal_type = 'nutrition'
    
    # Hydration
    elif any(word in combined_text for word in ['water', 'bottles', 'gallons', 'hydration', 'reminders', 
                                                  'consistency', 'desk', 'routine', 'soda reduction', 'drink more water',
                                                  'water reminder app', 'track intake', 'daily goal', 'spread throughout day',
                                                  'hydro flask', 'water intake', 'plant nanny', 'drink', 'hydrate',
                                                  '100 oz', 'tracking hydration']):
        goal_type = 'hydration'
    
    # Physical Activity / Exercise
    elif any(word in combined_text for word in ['workouts', 'walking', 'mindful walking', 'running', 'yoga', 
                                                  'stretching', 'strength training', 'cardio', 'flexibility', 
                                                  'outdoor activity', 'hiking', 'dog walks', 'pilates', 'crossfit', 
                                                  'gym', 'home workouts', 'accountability', 'apple watch', 'tracking',
                                                  'exercise', 'workout', 'physical', 'muscular legs', 'workout consistency',
                                                  'milestones', 'fitness goal', 'steps', 'neighborhood', 'active',
                                                  'physically active', 'endorphins', '30 minutes', '45 minutes',
                                                  'elliptical', 'weights', 'jumping jacks', 'treadmill', 'bike ride',
                                                  'jogging', 'run', 'jog', 'stamina', 'sunlight', 'vitamin d',
                                                  'personal trainer', 'swimming', 'dancing', 'toned', 'abs', 'legs',
                                                  'movement', 'bloggers', 'heart rate']):
        goal_type = 'physical_activity'
    
    # Stress Management / Mental Health
    elif any(word in combined_text for word in ['stress level', 'meditation', 'guided', 'unguided', 
                                                  'walking meditation', 'mindfulness', 'deep breathing', 
                                                  'self-care', 'reflection', 'journaling', 'sleep routine', 
                                                  'coping strategies', 'burnout', 'confidence', 'self-kindness', 
                                                  'resilience', 'motivational texts', 'positive reinforcement', 
                                                  'anxiety', 'overwhelm', 'stress', 'anxious', 'overwhelmed',
                                                  'limit soda', 'reduce sugary drinks', 'accountability buddy',
                                                  'problem solving', 'stress management', 'weekly check-ins',
                                                  'mental health', 'spiritual health', 'balance', 'feel better',
                                                  'well-being', 'mindful', 'headspace', 'youtube meditation',
                                                  'decompression', 'mental clarity', 'reducing anxiety', 'calm',
                                                  'mood', 'workload', 'empowerment', 'focus', 'patience',
                                                  'lazy', 'nervous', 'inner-child', 'breathing', 'grateful',
                                                  'joy', 'present', 'self-esteem', 'crying', 'unmotivated',
                                                  'depression', 'positive', 'connection with self', 'good nerves',
                                                  'venting', 'relax', 'art', 'painting', 'landscape', 'spirituality',
                                                  'clear thoughts', 'finals', 'manage workload', 'boundaries',
                                                  'setting boundaries', 'personal space', 'alone time', 'communicate']):
        goal_type = 'stress_management'
    
    # Self-Care / Leisure / Wellbeing
    elif any(word in combined_text for word in ['baths', 'disconnecting', 'screens', 'reading', 'me-time', 
                                                  'volunteer boundaries', 'enjoyable activities', 'fun', 'singing', 
                                                  'relaxation', 'personal growth', 'spiritual well-being', 
                                                  'self-esteem', 'body respect', 'guilt reduction', 'mental well-being',
                                                  'empowerment', 'health and wellness', 'mindful of well-being',
                                                  'vacation', 'travel', 'joshua tree', 'san diego', 'hawaii', 'oahu',
                                                  'mexico', 'salamanca', 'italy', 'milan', 'books', 'pleasure',
                                                  'escape', 'fantasy', 'memoir', 'comic', 'take yourself on a date',
                                                  'quiet time', 'hug', 'nature', 'visualization', 'tattoo']):
        goal_type = 'self_care'
    
    # Goal Setting / Accountability
    elif any(word in combined_text for word in ['smart goals', 'checklists', 'daily tracking', 'weekly tracking', 
                                                  'prioritization', 'program engagement', 'progress rating', 
                                                  'achievable steps', 'time blocking', 'calendar scheduling',
                                                  'goal', 'goals', 'measurable', 'attainable', 'relevant', 'timely',
                                                  'small achievable goals', 'habit formation', 'planning ahead',
                                                  'self-efficacy', 'habit reinforcement', 'overcoming disconnect',
                                                  'knowledge and action', 'accountability', 'check in', 'reminder',
                                                  'follow-through', 'determination', 'track', 'motivation', 'planner',
                                                  'sticky notes', 'whiteboard', 'dry erase', 'mirror', 'vanity',
                                                  'alarm', 'text messages', 'calendar invites', 'reminders',
                                                  'confidence rating', 'tracking progress', 'managing goals',
                                                  'challenge', 'execution', 'skills', 'routine', 'consistency',
                                                  'rhythm', 'structure', 'plan']):
        goal_type = 'goal_setting'
    
    # Time Management / Productivity
    elif any(word in combined_text for word in ['scheduling', 'blocking tasks', 'planning ahead', 'balancing', 
                                                  'school', 'work', 'family', 'unexpected tasks', 'multi-tasking', 
                                                  'deadlines', 'daily routines', 'maintaining structure', 'time management',
                                                  'telehealth job', 'long days', 'morning prep', 'balancing obligations',
                                                  'class schedule', 'flexible intervention', 'weekend adjustments',
                                                  'productive', 'compartmentalize', 'notifications', 'appointments',
                                                  'medical bills', 'calendar management', 'busy week', 'campaign work',
                                                  'public speaking', 'scheduling walks', 'prioritizing achievable goals',
                                                  'desk use', 'not working in bed', 'clutter reduction', 'workspace organization',
                                                  'separate work/life', 'ergonomics', 'office setup', 'commute', 'break',
                                                  'emails', 'assignments', 'project', 'presentation', 'homework',
                                                  'tutoring', 'practicum', 'office', 'class', 'neurobiology',
                                                  'gpa', 'undergraduate', 'usf', 'advisor', 'shadowing', 'pediatrician',
                                                  'semester', 'hectic', 'test', 'presentations']):
        goal_type = 'time_management'
    
    # Social / Family Connections
    elif any(word in combined_text for word in ['friends', 'family', 'quality time', 'calls', 'meetups', 
                                                  'email', 'relationships', 'social support', 'community', 
                                                  'interactions', 'engagement', 'celebrating milestones', 'social',
                                                  'walking with friend', 'parent support', 'support from campaign team',
                                                  'dealing with pet loss', 'cultural responsibilities', 'familial responsibilities',
                                                  'helping others', 'research', 'partner', 'boyfriend', 'internship',
                                                  'roommate', 'coach', 'messages', 'border', 'cousins', 'brother',
                                                  'dad', 'mom', 'home', 'cat', 'taiga', 'cat mom', 'dog',
                                                  'emotional support']):
        goal_type = 'social_connections'
    
    # Health Monitoring / Medical Care
    elif any(word in combined_text for word in ['glucose', 'diabetes', 'blood work', 'fertility', 'ob-gyn', 
                                                  'appointments', 'women\'s health', 'pcp', 'vaccination', 
                                                  'allergies', 'checkups', 'type 1 diabetes', 'medical', 'doctor',
                                                  'vaccine', 'cold', 'achy', 'congested', 'recovery', 'antibiotics',
                                                  'treatment', 'cornea', 'photophobia', 'light sensitivity',
                                                  'eyes', 'eye health', 'medical school', 'entrance exam',
                                                  'pediatrics', 'vet', 'seizures', 'scary', 'migraine', 'headache']):
        goal_type = 'health_monitoring'
    
    # Energy / Fatigue / Long-term Goals
    elif any(word in combined_text for word in ['energy', 'exhaustion', 'naps', 'sleep quality', 'immune system', 
                                                  'migraine', 'clinical training', 'semester', 'long-term wellness', 
                                                  'prevention', 'fatigue', 'tired', 'managing energy', 'decompressing',
                                                  'returning refreshed', 'avoiding fatigue', 'crash prevention',
                                                  'well-rested', 'energetic', 'productive', 'motivated', 'feel better',
                                                  'more energy', 'wake-up routine', 'reduce caffeine', 'cascading effect']):
        goal_type = 'energy_management'
    
    # Sleep & Rest
    elif any(word in combined_text for word in ['sleep', 'bedtime', 'wind-down', 'screens off', 'phone away',
                                                  'brush teeth', 'use bathroom', 'lights off', 'consistent schedule',
                                                  'energy restoration', 'restful sleep', 'reduce late-night activity',
                                                  'midnight alarm', 'morning alarm', 'sleep routine', 'sleep late',
                                                  'woke', 'rest', 'phone-free', 'old book', 'laptop', 'social media',
                                                  'refresh', 'decompress', 'bed', 'sleeping', 'resting',
                                                  'healthy sleep', 'sleep schedule', 'prioritize']):
        goal_type = 'sleep_rest'
    
    # Cooking / Meal Prep
    elif any(word in combined_text for word in ['cooking', 'meal prep', 'make-ahead meals', 'practical portions', 
                                                  'healthy recipes', 'avoiding takeout', 'experimenting recipes',
                                                  'takeout', 'prep', 'groceries', 'leftovers', 'cook', 'meal plan',
                                                  'reduce waste', 'save money', 'grocery planning', 'food waste']):
        goal_type = 'cooking'
    
    # Determine context with expanded categories
    context = 'general'
    
    # Confidence Assessment
    if any(phrase in coach_lower for phrase in ['scale of', 'rate yourself', 'rate your', 'how confident', 
                                                  'confidence level', 'scale from', '1 to 10', 'one to ten',
                                                  'how sure', 'certain are you', 'belief in', 'faith in your ability',
                                                  'gauge your', 'assess your', 'measure your confidence',
                                                  'where do you fall', 'rank yourself', 'self-rating', 'self-assessment',
                                                  'how likely', 'probability', 'chances are', 'odds of',
                                                  'conviction', 'assurance', 'certainty level', 'degree of confidence',
                                                  'how strongly', 'firmly believe', 'secure in your ability']):
        context = 'confidence_assessment'
    
    # Goal Setting
    elif any(phrase in coach_lower for phrase in ['goal', 'thinking about', 'plan', 'set a goal', 'work towards',
                                                    'what would you like', 'want to achieve', 'hoping to', 'aiming for',
                                                    'target', 'objective', 'intention', 'smart goal', 'specific goal',
                                                    'measurable', 'steps you', 'action plan', 'envision', 'vision',
                                                    'outcome', 'result', 'end result', 'desired outcome', 'aspiration',
                                                    'ambition', 'purpose', 'aim', 'milestone', 'benchmark',
                                                    'what do you hope', 'looking to accomplish', 'striving for',
                                                    'working on', 'focusing on', 'priority goal', 'main goal',
                                                    'long-term goal', 'short-term goal', 'weekly goal', 'daily goal',
                                                    'realistic goal', 'attainable', 'time-bound', 'deadline',
                                                    'commitment', 'promise to yourself', 'dedicate to']):
        context = 'goal_setting'
    
    # Barrier Identification
    elif any(phrase in coach_lower for phrase in ['barrier', 'challenge', 'difficult', 'obstacle', 'getting in the way',
                                                    'preventing you', 'stopping you', 'struggle', 'hard time',
                                                    'what makes it', 'interference', 'roadblock', 'difficulty',
                                                    'problem', 'issue', 'concern', 'worry about', 'complication',
                                                    'impediment', 'hindrance', 'hurdle', 'setback', 'snag',
                                                    'constraint', 'limitation', 'restriction', 'what stands in',
                                                    'holds you back', 'gets in your way', 'makes it tough',
                                                    'makes it challenging', 'interferes', 'blocks you', 'trips you up',
                                                    'stumbling block', 'pain point', 'friction', 'resistance',
                                                    'what prevents', 'what keeps you from', 'stands between you',
                                                    'working against', 'competing with', 'conflict']):
        context = 'barrier_identification'
    
    # Progress Review
    elif any(phrase in coach_lower for phrase in ['how was', 'progress', 'worked out', 'week', 'how did', 'went well',
                                                    'accomplish', 'achieve', 'complete', 'follow through', 'did you',
                                                    'were you able', 'success', 'how many times', 'tracking',
                                                    'review', 'looking back', 'reflection', 'update me', 'catch up',
                                                    'check-in', 'status', 'where are you', 'how far', 'advancement',
                                                    'movement', 'improvement', 'growth', 'development', 'evolution',
                                                    'gains', 'wins', 'victories', 'accomplishments', 'milestones reached',
                                                    'since last time', 'since we talked', 'past week', 'past few days',
                                                    'how things went', 'outcome', 'results', 'performance',
                                                    'follow up', 'touch base', 'report back', 'debrief',
                                                    'what happened', 'how it turned out', 'end up', 'work out',
                                                    'stick to', 'maintain', 'keep up', 'consistency']):
        context = 'progress_review'
    
    # Greeting
    elif any(phrase in coach_lower for phrase in ['hello', 'how are you', 'hi there', 'good morning', 'good afternoon',
                                                    'good evening', 'nice to see', 'welcome', 'thanks for joining',
                                                    'glad to connect', 'how have you been', 'greetings',
                                                    'pleasure to', 'great to see', 'wonderful to', 'happy to',
                                                    'hey', 'howdy', 'good to see', 'nice to talk',
                                                    'appreciate you', 'thank you for', 'glad you could',
                                                    'excited to', 'looking forward', 'delighted to']):
        context = 'greeting'
    
    # Coach Assessing State of Change
    elif any(phrase in coach_lower for phrase in ['ready', 'prepared', 'change', 'stage', 'willing', 'motivation',
                                                    'committed', 'dedication', 'interested in', 'open to',
                                                    'considering', 'thinking about making', 'readiness',
                                                    'feel about starting', 'important to you', 'priority',
                                                    'motivated', 'driven', 'inspired', 'determined', 'resolved',
                                                    'eager', 'enthusiastic', 'passionate', 'devoted', 'dedicated',
                                                    'serious about', 'intent on', 'focused on changing',
                                                    'desire to', 'want to', 'wish to', 'hope to',
                                                    'contemplating', 'mulling over', 'weighing', 'evaluating',
                                                    'receptive', 'amenable', 'agreeable', 'inclined',
                                                    'stage of change', 'precontemplation', 'contemplation', 'preparation',
                                                    'action stage', 'maintenance', 'where you are in']):
        context = 'coach_assessing_state_of_change'
    
    # Establishing Agenda
    elif any(phrase in coach_lower for phrase in ['agenda', 'today', 'focus on', 'discuss', 'check in about',
                                                    'talk about', 'cover', 'address', 'work on', 'session',
                                                    'what would you like', 'priorities', 'topics', 'main thing',
                                                    'start with', 'begin by', 'dive into', 'explore',
                                                    'concentrate on', 'devote time', 'spend time on',
                                                    'meeting', 'conversation', 'dialogue', 'chat about',
                                                    'bring up', 'touch on', 'go over', 'review together',
                                                    'plan for today', 'outline', 'structure', 'format',
                                                    'what brings you', 'reason for', 'purpose of',
                                                    'main focus', 'primary concern', 'top priority',
                                                    'what matters most', 'pressing issue', 'immediate need']):
        context = 'establishing_agenda'
    
    # Confidence to Reach Goals
    elif any(phrase in coach_lower for phrase in ['confidence', 'confident', 'able to do', 'reach your goal',
                                                    'achieve this', 'capability', 'believe you can', 'trust yourself',
                                                    'faith in yourself', 'successful', 'accomplish this',
                                                    'make it happen', 'follow through', 'stick with',
                                                    'capacity', 'competence', 'ability', 'skill', 'potential',
                                                    'self-efficacy', 'self-belief', 'self-assurance', 'self-trust',
                                                    'see yourself', 'envision yourself', 'picture yourself',
                                                    'count on yourself', 'rely on yourself', 'depend on yourself',
                                                    'pull it off', 'get it done', 'make progress', 'move forward',
                                                    'succeed', 'prevail', 'triumph', 'victory', 'win',
                                                    'capable of', 'equipped to', 'prepared to', 'ready to',
                                                    'strong enough', 'resilient', 'persistent', 'determined']):
        context = 'confidence_to_reach_goals'
    
    # Measuring Stress Level
    elif any(phrase in coach_lower for phrase in ['stress', 'stressed', 'overwhelmed', 'feeling', 'stress level',
                                                    'anxious', 'anxiety', 'pressure', 'tension', 'burnout',
                                                    'coping', 'managing', 'handling', 'dealing with', 'emotional state',
                                                    'mental health', 'wellbeing', 'well-being', 'mental state',
                                                    'frazzled', 'frantic', 'hectic', 'chaotic', 'crazy',
                                                    'swamped', 'buried', 'drowning', 'under water',
                                                    'breaking point', 'at capacity', 'maxed out', 'exhausted',
                                                    'drained', 'depleted', 'worn out', 'fatigued', 'tired',
                                                    'strained', 'taxed', 'burdened', 'weighed down',
                                                    'nervous', 'worried', 'concerned', 'uneasy', 'troubled',
                                                    'distressed', 'agitated', 'restless', 'on edge',
                                                    'how are you feeling', 'emotional well-being', 'mood',
                                                    'peace of mind', 'calm', 'relaxed', 'centered', 'balanced']):
        context = 'measuring_stress_level'
    
    # Support Needed for Goals
    elif any(phrase in coach_lower for phrase in ['support', 'help', 'need', 'assistance', 'resources',
                                                    'what can i', 'how can i', 'tools', 'strategies',
                                                    'guidance', 'advice', 'suggestions', 'tips', 'recommend',
                                                    'provide you', 'offer', 'facilitate', 'enable',
                                                    'aid', 'back you up', 'be there for', 'assist you',
                                                    'encourage', 'motivate', 'inspire', 'empower',
                                                    'equip you', 'arm you with', 'give you', 'share with you',
                                                    'information', 'knowledge', 'education', 'training',
                                                    'coaching', 'mentoring', 'counseling', 'advising',
                                                    'ideas', 'options', 'alternatives', 'approaches',
                                                    'techniques', 'methods', 'tactics', 'practices',
                                                    'what would help', 'what do you need', 'require',
                                                    'beneficial', 'useful', 'helpful', 'valuable',
                                                    'accountability', 'check-ins', 'reminders', 'prompts',
                                                    'structure', 'framework', 'system', 'plan']):
        context = 'support_needed_for_goals'
    
    # Estimate confidence level
    confidence = 7  # default

    # Check for numeric values (including decimals like 7.5, 8.5, etc.)
    number_match = re.search(r'\b(\d+(?:\.\d+)?)\b', participant_lower)
    if number_match:
        num = float(number_match.group(1))
        if 1 <= num <= 10:
            confidence = num
    # Check for written numbers
    elif 'one' in participant_lower:
        confidence = 1
    elif 'two' in participant_lower:
        confidence = 2
    elif 'three' in participant_lower:
        confidence = 3
    elif 'four' in participant_lower:
        confidence = 4
    elif 'five' in participant_lower:
        confidence = 5
    elif 'six' in participant_lower:
        confidence = 6
    elif 'seven' in participant_lower:
        confidence = 7
    elif 'eight' in participant_lower:
        confidence = 8
    elif 'nine' in participant_lower:
        confidence = 9
    elif 'ten' in participant_lower:
        confidence = 10
    # Qualitative assessments
    elif any(word in participant_lower for word in ['confident', 'easy', 'easily', 'definitely']):
        confidence = 8
    elif any(word in participant_lower for word in ['hard', 'difficult', 'challenging', 'nervous']):
        confidence = 5
    
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