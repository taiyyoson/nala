from openai import OpenAI
from anthropic import Anthropic
from query import VectorSearch
import os
from dotenv import load_dotenv
import time

load_dotenv()

class UnifiedRAGChatbot:
    """RAG chatbot that supports multiple LLM providers"""
    
    AVAILABLE_MODELS = {
        # OpenAI models
        'gpt-4o': {'provider': 'openai', 'name': 'GPT-4o'},
        'gpt-4o-mini': {'provider': 'openai', 'name': 'GPT-4o Mini'},
        'gpt-4-turbo': {'provider': 'openai', 'name': 'GPT-4 Turbo'},
        
        # Claude models
        'claude-opus-4': {'provider': 'anthropic', 'name': 'Claude Opus 4', 'model_id': 'claude-opus-4-20250514'},
        'claude-sonnet-4': {'provider': 'anthropic', 'name': 'Claude Sonnet 4', 'model_id': 'claude-sonnet-4-20250514'},
        'claude-sonnet-4.5': {'provider': 'anthropic', 'name': 'Claude Sonnet 4.5', 'model_id': 'claude-sonnet-4-5-20250929'},
    }
    
    def __init__(self, model='claude-sonnet-4.5', top_k=3):
        """
        Initialize unified RAG system
        
        Args:
            model: Model name from AVAILABLE_MODELS
            top_k: Number of similar examples to retrieve
        """
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model}' not supported. Choose from: {list(self.AVAILABLE_MODELS.keys())}")
        
        self.model = model
        self.model_info = self.AVAILABLE_MODELS[model]
        self.top_k = top_k
        self.searcher = VectorSearch()
        self.conversation_history = []
        
        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None
        
        if self.model_info['provider'] == 'openai':
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.model_info['provider'] == 'anthropic':
            self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def retrieve(self, query, min_similarity=0.4):
        """
        Retrieve relevant coaching examples from vector database
        """
        # TEST: Use pure vector search instead of hybrid
        results = self.searcher.search_with_details(
            query, 
            limit=self.top_k,
            min_similarity=min_similarity
        )
        return results
    
    def build_context(self, retrieved_examples):
        """
        Build context string from retrieved examples
        """
        if not retrieved_examples:
            return "No relevant examples found in the database."
        
        context = "Here are relevant coaching conversation examples:\n\n"
        
        for i, example in enumerate(retrieved_examples, 1):
            # Handle both regular search and hybrid search formats
            similarity = example.get('combined_score') or example.get('similarity') or example.get('vector_similarity', 0)
            
            context += f"Example {i} (similarity: {similarity:.2f}):\n"
            context += f"Participant: {example['participant_response']}\n"
            context += f"Coach: {example['coach_response']}\n"
            context += f"Context: {example['category']} | Goal: {example['goal_type']}\n\n"
        
        return context
    
    def get_system_prompt(self, context):
        """Get system prompt with context"""
        return f"""You are a supportive health and wellness coach. Your coaching style should be:
- Warm, empathetic, and encouraging
- Ask open-ended questions to promote reflection
- Help users set SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound)
- Acknowledge their feelings and validate their experiences
- Provide actionable suggestions based on their specific situation
- Celebrate their wins and progress
- Keep responses concise and conversational (2-4 sentences)
- Ask only 1 question at a time

{context}

Use these examples as guidance for your coaching style and responses. Mirror the supportive, questioning approach shown by the coach in the examples."""
    
    def generate_with_openai(self, user_message, system_prompt):
        """Generate response using OpenAI"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if self.conversation_history:
            messages.extend(self.conversation_history[-6:])
        
        messages.append({"role": "user", "content": user_message})
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )
        
        return response.choices[0].message.content
    
    def generate_with_anthropic(self, user_message, system_prompt):
        """Generate response using Anthropic Claude with prompt caching"""
        messages = []
        
        if self.conversation_history:
            messages.extend(self.conversation_history[-6:])
        
        messages.append({"role": "user", "content": user_message})
        
        model_id = self.model_info.get('model_id', self.model)
        
        response = self.anthropic_client.messages.create(
            model=model_id,
            max_tokens=500,
            temperature=0.7,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}  # Cache this!
                }
            ],
            messages=messages
        )
        
        return response.content[0].text
    
    def generate_with_anthropic_streaming(self, user_message, system_prompt):
        """Generate streaming response with prompt caching"""
        messages = []
        
        if self.conversation_history:
            messages.extend(self.conversation_history[-6:])
        
        messages.append({"role": "user", "content": user_message})
        
        model_id = self.model_info.get('model_id', self.model)
        
        # Stream with prompt caching
        full_response = ""
        with self.anthropic_client.messages.stream(
            model=model_id,
            max_tokens=500,
            temperature=0.7,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}  # Cache the system prompt!
                }
            ],
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full_response += text
        
        return full_response
        
    def generate_response(self, user_message, use_history=True):
        """Generate response using RAG pipeline with timing"""
        
        # Retrieve relevant examples
        retrieved_examples = self.retrieve(user_message)
        
        # Build context
        context = self.build_context(retrieved_examples)
        system_prompt = self.get_system_prompt(context)
        
        # Generate based on provider
        if self.model_info['provider'] == 'openai':
            response = self.generate_with_openai(user_message, system_prompt)
        elif self.model_info['provider'] == 'anthropic':
            response = self.generate_with_anthropic_streaming(user_message, system_prompt)  # Changed!
        
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
    
    
    def switch_model(self, new_model):
        """Switch to a different model"""
        if new_model not in self.AVAILABLE_MODELS:
            print(f"Model '{new_model}' not available.")
            print(f"Available models: {list(self.AVAILABLE_MODELS.keys())}")
            return False
        
        self.model = new_model
        self.model_info = self.AVAILABLE_MODELS[new_model]
        
        # Initialize new client if needed
        if self.model_info['provider'] == 'openai' and not self.openai_client:
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.model_info['provider'] == 'anthropic' and not self.anthropic_client:
            self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        print(f"✓ Switched to {self.model_info['name']}")
        return True
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("Conversation history cleared.")


def compare_models(query, models=None):
    """
    Compare how different models respond to the same query
    
    Args:
        query: The query to test
        models: List of model names to compare (default: all)
    """
    if models is None:
        models = ['gpt-4o-mini', 'gpt-4o', 'claude-sonnet-4', 'claude-sonnet-4.5']
    
    print("=" * 80)
    print(f"COMPARING MODELS")
    print("=" * 80)
    print(f"\nQuery: {query}\n")
    
    for model in models:
        try:
            print("-" * 80)
            chatbot = UnifiedRAGChatbot(model=model, top_k=3)
            response, sources, model_name = chatbot.generate_response(query, use_history=False)
            
            print(f"\n{model_name}:")
            print(f"{response}\n")
            
        except Exception as e:
            print(f"\n{model} - Error: {e}\n")


def interactive_chat():
    """Interactive chat with model switching"""
    print("=" * 80)
    print("Unified RAG Chatbot - Multi-Model Support")
    print("=" * 80)
    
    # Show available models
    print("\nAvailable models:")
    for key, info in UnifiedRAGChatbot.AVAILABLE_MODELS.items():
        print(f"  {key}: {info['name']}")
    
    print("\nCommands:")
    print("  'switch <model>' - Switch to different model")
    print("  'compare' - Compare current query across all models")
    print("  'sources' - Show retrieved sources for next response")
    print("  'reset' - Clear conversation history")
    print("  'models' - List available models")
    print("  'quit' - Exit")
    print("\n" + "=" * 80 + "\n")
    
    # Start with default model
    chatbot = UnifiedRAGChatbot(model='claude-sonnet-4.5')
    print(f"Current model: {chatbot.model_info['name']}\n")
    
    show_sources = False
    last_query = None
    
    while True:
        user_input = input("You: ").strip()
        
        
        if not user_input:
            continue
        
        # Handle commands
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nThanks for chatting!")
            break
        
        if user_input.lower() == 'reset':
            chatbot.reset_conversation()
            continue
        
        if user_input.lower() == 'models':
            print("\nAvailable models:")
            for key, info in UnifiedRAGChatbot.AVAILABLE_MODELS.items():
                current = " (current)" if key == chatbot.model else ""
                print(f"  {key}: {info['name']}{current}")
            print()
            continue
        
        if user_input.lower() == 'sources':
            show_sources = True
            print("Will show sources for next response...")
            continue
        
        if user_input.lower().startswith('switch '):
            new_model = user_input[7:].strip()
            chatbot.switch_model(new_model)
            continue
        
        if user_input.lower() == 'compare':
            if last_query:
                compare_models(last_query)
            else:
                print("No previous query to compare. Ask a question first!")
            continue
        
        start = time.time()

        # Generate response
        try:
            last_query = user_input
            start = time.time()
            
            response, sources, model_name = chatbot.generate_response(user_input)
            
            if show_sources:
                print("\n--- Retrieved Sources ---")
                for i, source in enumerate(sources, 1):
                    print(f"\nSource {i} (similarity: {source['similarity']:.3f}):")
                    print(f"Category: {source['category']}")
                    print(f"Participant: {source['participant_response'][:100]}...")
                    print(f"Coach: {source['coach_response'][:100]}...")
                print("\n--- Response ---")
            
            # REMOVE OR COMMENT OUT THIS LINE - it's duplicating the streamed output:
            # print(f"\nCoach [{model_name}]: {response}\n")
            
            # Instead, just add a newline after streaming and the timing info:
            print()  # Blank line for spacing
            

        except Exception as e:
            print(f"\nError: {e}\n")
        
        show_sources = False


if __name__ == "__main__":
    interactive_chat()