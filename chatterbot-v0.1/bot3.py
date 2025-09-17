from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from chatterbot.logic import BestMatch
from chatterbot.comparisons import LevenshteinDistance
import re
import logging

# Configure logging
# logging.basicConfig(level=logging.INFO)

class HealthCoachingBot:
    def __init__(self, name="HealthCoach", corpus_file="health-training-data.txt"):
        self.corpus_file = corpus_file
        
        # Initialize chatbot with focus on similarity matching
        self.chatbot = ChatBot(
            name,
            storage_adapter='chatterbot.storage.SQLStorageAdapter',
            database_uri='sqlite:///health_coach_db.sqlite3',
            logic_adapters=[
                {
                    'import_path': 'chatterbot.logic.BestMatch',
                    'default_response': "That's interesting. Can you tell me more about that?",
                    'maximum_similarity_threshold': 0.85,
                    'statement_comparison_function': LevenshteinDistance
                }
            ],
            preprocessors=[
                'chatterbot.preprocessors.clean_whitespace',
                'chatterbot.preprocessors.convert_to_ascii'
            ]
        )
        
        self.trainer = ListTrainer(self.chatbot)
        
    def parse_health_coaching_data(self):
        """Parse the health coaching dialogue format with proper role separation"""
        try:
            with open(self.corpus_file, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            print(f"Warning: {self.corpus_file} not found.")
            return []
        except Exception as e:
            print(f"Error reading {self.corpus_file}: {e}")
            return []
        
        conversations = []
        
        # Split by lines and process each line
        lines = content.split('\n')
        sequence = []
        current_message = []
        current_role = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with a role indicator
            if line.startswith('Health Coach:'):
                # Save previous message if exists
                if current_role and current_message:
                    message = ' '.join(current_message).strip()
                    clean_msg = self.clean_message(message)
                    if clean_msg:
                        sequence.append((current_role, clean_msg))
                
                # Start new coach message
                current_role = "coach"
                current_message = [line[13:].strip()]  # Remove "Health Coach:" prefix
                
            elif line.startswith('Participant:'):
                # Save previous message if exists
                if current_role and current_message:
                    message = ' '.join(current_message).strip()
                    clean_msg = self.clean_message(message)
                    if clean_msg:
                        sequence.append((current_role, clean_msg))
                
                # Start new participant message
                current_role = "participant"
                current_message = [line[12:].strip()]  # Remove "Participant:" prefix
                
            else:
                # Continuation of current message
                if current_role and line:
                    current_message.append(line)
        
        # Don't forget the last message
        if current_role and current_message:
            message = ' '.join(current_message).strip()
            clean_msg = self.clean_message(message)
            if clean_msg:
                sequence.append((current_role, clean_msg))
        
        # Convert sequence to training pairs
        # We want: when user says something like participant, bot responds like coach
        for i in range(len(sequence) - 1):
            current_role, current_msg = sequence[i]
            next_role, next_msg = sequence[i + 1]
            
            if current_role == "participant" and next_role == "coach":
                # Participant -> Coach: User input -> Bot response
                conversations.extend([current_msg, next_msg])
        
        return conversations
    
    def clean_message(self, message):
        """Clean individual messages while preserving coaching tone"""
        if not message:
            return ""
        
        # Remove any remaining role indicators that might have been caught
        message = re.sub(r'^(Health Coach|Participant):\s*', '', message, flags=re.IGNORECASE)
        
        # Remove extra whitespace but preserve single line breaks
        message = re.sub(r'[ \t]+', ' ', message)  # Replace multiple spaces/tabs with single space
        message = re.sub(r'\n\s*\n', '\n', message)  # Replace multiple newlines with single
        
        # Remove very short or empty messages
        if len(message.strip()) < 5:
            return ""
        
        return message.strip()
    
    def train_bot(self):
        """Train the bot with health coaching conversations"""
        print("Parsing health coaching conversations...")
        conversations = self.parse_health_coaching_data()
        
        if not conversations:
            print("No valid conversations found. Adding minimal training data.")
            # Add minimal health coaching style responses
            conversations = [
                "Hi", "Hello! I'm here to help you with your health goals. What would you like to work on today?",
                "Hello", "Hi there! Let's talk about your health and wellness. What's on your mind?",
                "I want to be healthier", "That's a great goal! Can you tell me more specifically what aspect of your health you'd like to focus on?",
                "I need help", "I'm here to help you. What specific area of your health or wellness would you like to work on?",
            ]
        
        print(f"Training with {len(conversations)//2} conversation pairs...")
        
        # Train the chatbot
        self.trainer.train(conversations)
        
        print("Training completed!")
    
    def get_response(self, user_input):
        """Get response from the trained health coaching bot"""
        try:
            response = self.chatbot.get_response(user_input)
            response_text = str(response)
            
            # Clean up any duplicate "Health Coach:" prefixes in the response
            response_text = re.sub(r'Health Coach:\s*', '', response_text, flags=re.IGNORECASE)
            
            # Remove any accidental duplications or concatenations
            # Split by common duplication patterns and take the first clean part
            if 'Health Coach:' in response_text:
                parts = response_text.split('Health Coach:')
                response_text = parts[0].strip()
            
            # Ensure response doesn't start with role indicators
            response_text = re.sub(r'^(Health Coach|Participant):\s*', '', response_text, flags=re.IGNORECASE)
            
            return response_text.strip()
            
        except Exception as e:
            print(f"Error getting response: {e}")
            return "I'd like to help you with that. Can you tell me more about what you're thinking?"
    
    def analyze_training_data(self):
        """Analyze the quality and content of training data"""
        conversations = self.parse_health_coaching_data()
        
        if not conversations:
            return "No training data found."
        
        total_pairs = len(conversations) // 2
        
        # Analyze common coaching phrases
        all_coach_responses = [conversations[i] for i in range(1, len(conversations), 2)]
        common_coaching_words = {}
        
        coaching_keywords = ['goal', 'specific', 'tell me', 'why', 'important', 'how', 'what', 'can you', 'help', 'focus']
        
        for response in all_coach_responses:
            response_lower = response.lower()
            for keyword in coaching_keywords:
                if keyword in response_lower:
                    common_coaching_words[keyword] = common_coaching_words.get(keyword, 0) + 1
        
        analysis = f"""
Training Data Analysis:
- Total conversation pairs: {total_pairs}
- Average response length: {sum(len(r.split()) for r in all_coach_responses) / len(all_coach_responses):.1f} words
- Common coaching phrases found: {dict(sorted(common_coaching_words.items(), key=lambda x: x[1], reverse=True))}
        """
        
        return analysis.strip()

def main():
    """Main function to run the health coaching chatbot"""
    print("Initializing Health Coaching Chatbot...")
    print("This bot learns from Health Coach <-> Participant conversations")
    print("-" * 60)
    
    # Initialize the bot
    bot = HealthCoachingBot()
    
    # Train the bot
    bot.train_bot()
    
    # Show training analysis
    print("\n" + bot.analyze_training_data())
    
    print("\nHealth Coaching Bot is ready!")
    print("The bot will respond in the style of a health coach based on your training data.")
    print("Type 'analyze' to see training data analysis")
    print("Type 'q', 'quit', or 'exit' to end the conversation")
    print("-" * 60)
    
    exit_conditions = ("q", "quit", "exit")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in exit_conditions:
                print("Health Coach: Take care and remember to work on your health goals! Goodbye!")
                break
            elif user_input.lower() == 'analyze':
                print(bot.analyze_training_data())
                continue
            elif not user_input:
                print("Health Coach: I'm here to listen. What would you like to talk about?")
                continue
            
            # Get response from the bot
            response = bot.get_response(user_input)
            print(f"Health Coach: {response}")
            
        except KeyboardInterrupt:
            print("\nHealth Coach: Take care! Remember to focus on your health goals!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Health Coach: Let's try that again. What would you like to discuss?")

if __name__ == "__main__":
    main()