import openai
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root .env file
_root_dir = Path(__file__).parent.parent
_env_file = _root_dir / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

class VectorSearch:
    """Vector search module for coaching conversations database"""
    
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai        
    def get_db_connection(self):
    
        database_url = os.getenv('DATABASE_URL')
    
        if database_url:
            # Use DATABASE_URL (Render/production)
            return psycopg2.connect(database_url)
        else:
            # Use individual parameters (local development)
            return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'chatbot_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
    
    def detect_context(self, query):
        """
        Automatically detect likely context from query keywords
        Returns best guess for context enhancement
        """
        query_lower = query.lower()
        
        # Map keywords to contexts
        context_keywords = {
            'stress_management': ['stress', 'anxious', 'overwhelmed', 'worried', 'nervous', 'calm', 'relax', 'anxiety', 'tension'],
            'nutrition': ['eat', 'food', 'meal', 'diet', 'nutrition', 'hungry', 'cooking', 'recipe', 'healthy eating'],
            'physical_activity': ['exercise', 'workout', 'walk', 'run', 'gym', 'active', 'fitness', 'movement', 'training'],
            'sleep_rest': ['sleep', 'tired', 'rest', 'exhausted', 'bedtime', 'insomnia', 'fatigue'],
            'goal_setting': ['goal', 'plan', 'achieve', 'accomplish', 'target', 'objective', 'progress'],
            'hydration': ['water', 'drink', 'hydrate', 'hydration', 'thirsty'],
            'self_care': ['self-care', 'relax', 'meditation', 'mindfulness', 'wellness', 'wellbeing'],
        }
        
        # Check which context matches best
        for context, keywords in context_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return context
        
        return 'general'
    
    def search(self, query, limit=3, min_similarity=0.4, category_filter=None, auto_detect_context=True):
        """
        Search for relevant coaching conversations
        
        Args:
            query (str): User's search query
            limit (int): Maximum number of results to return
            min_similarity (float): Minimum similarity score (0-1)
            category_filter (str): Optional category to filter by
            auto_detect_context (bool): Automatically detect context from query
            
        Returns:
            list: List of tuples (participant_response, coach_response, 
                context_category, goal_type, similarity_score)
        """
        
        # === NEW: Auto-detect context if not provided ===
        if auto_detect_context and not category_filter:
            detected_context = self.detect_context(query)
            enhanced_query = f"Context: {detected_context} | Goal: {detected_context} | {query}"
        elif category_filter:
            enhanced_query = f"Context: {category_filter} | Goal: {category_filter} | {query}"
        else:
            enhanced_query = f"Context: general | Goal: general | {query}"
        
        # Generate embedding for enhanced query
        query_embedding = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=enhanced_query
        ).data[0].embedding
        
        # Rest stays the same...
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        sql = """
            SELECT 
                participant_response,
                coach_response,
                context_category,
                goal_type,
                1 - (participant_embedding <=> %s::vector) as similarity
            FROM coaching_conversations
            WHERE 1 - (participant_embedding <=> %s::vector) >= %s
        """
        params = [query_embedding, query_embedding, min_similarity]
        
        if category_filter:
            sql += " AND context_category = %s"
            params.append(category_filter)
        
        sql += """
            ORDER BY participant_embedding <=> %s::vector
            LIMIT %s
        """
        params.extend([query_embedding, limit])
        
        cur.execute(sql, params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return results
    
    def hybrid_search(self, query, limit=3, min_similarity=0.3, keyword_weight=0.3, category_filter=None):
        """
        Combine vector similarity with keyword matching for better results
        
        Args:
            query (str): User's search query
            limit (int): Maximum number of results to return
            min_similarity (float): Minimum similarity score (0-1)
            keyword_weight (float): How much to weight keyword matches (0-1)
            category_filter (str): Optional category to filter by
            
        Returns:
            list: List of tuples (participant_response, coach_response, 
                context_category, goal_type, combined_score, vector_score, keyword_score)
        """
        
        # Auto-detect context
        detected_context = self.detect_context(query)
        enhanced_query = f"Context: {detected_context} | Goal: {detected_context} | {query}"
        
        # Generate embedding for enhanced query
        query_embedding = self.client.Embedding.create(
            model="text-embedding-3-small",
            input=enhanced_query
        ).data[0].embedding
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Build hybrid search query
        sql = """
            WITH vector_scores AS (
                SELECT 
                    id,
                    participant_response,
                    coach_response,
                    context_category,
                    goal_type,
                    1 - (participant_embedding <=> %s::vector) as vector_similarity
                FROM coaching_conversations
                WHERE 1 - (participant_embedding <=> %s::vector) >= %s
            ),
            text_scores AS (
                SELECT 
                    id,
                    ts_rank(
                        to_tsvector('english', participant_response || ' ' || coach_response),
                        plainto_tsquery('english', %s)
                    ) as text_similarity
                FROM coaching_conversations
            )
            SELECT 
                v.participant_response,
                v.coach_response,
                v.context_category,
                v.goal_type,
                (v.vector_similarity * %s + COALESCE(t.text_similarity, 0) * %s) as combined_score,
                v.vector_similarity,
                COALESCE(t.text_similarity, 0) as keyword_score
            FROM vector_scores v
            LEFT JOIN text_scores t ON v.id = t.id
        """
        
        params = [
            query_embedding,
            query_embedding, 
            min_similarity,
            query,  # Original query for keyword search
            1 - keyword_weight,  # Vector weight
            keyword_weight       # Keyword weight
        ]
        
        # Add category filter if provided
        if category_filter:
            sql += " WHERE v.context_category = %s"
            params.append(category_filter)
        
        sql += """
            ORDER BY combined_score DESC
            LIMIT %s
        """
        params.append(limit)
        
        cur.execute(sql, params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return results
        
    def get_coach_responses(self, query, limit=3, min_similarity=0.4):
        """
        Convenience method - returns only coach responses
        
        Returns:
            list: List of coach response strings
        """
        results = self.search(query, limit, min_similarity)
        return [result[1] for result in results]
    
    def hybrid_search_with_details(self, query, limit=3, min_similarity=0.3, keyword_weight=0.3):
        """
        Returns hybrid search results as list of dictionaries for easier access
        
        Returns:
            list: List of dicts with keys: participant_response, coach_response,
                category, goal_type, combined_score, vector_score, keyword_score
        """
        results = self.hybrid_search(query, limit, min_similarity, keyword_weight)
        
        return [
            {
                'participant_response': r[0],
                'coach_response': r[1],
                'category': r[2],
                'goal_type': r[3],
                'combined_score': r[4],
                'vector_similarity': r[5],
                'keyword_score': r[6]
            }
            for r in results
        ]
    
    def search_with_details(self, query, limit=3, min_similarity=0.4):
        """
        Pure vector search (faster than hybrid) with detailed results
        """
        
        query_embedding = self.client.Embedding.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        sql = """
            SELECT 
                participant_response,
                coach_response,
                context_category,
                goal_type,
                1 - (participant_embedding <=> %s::vector) as similarity
            FROM coaching_conversations
            WHERE 1 - (participant_embedding <=> %s::vector) >= %s
            ORDER BY participant_embedding <=> %s::vector
            LIMIT %s
        """
        
        params = [query_embedding, query_embedding, min_similarity, query_embedding, limit]
        cur.execute(sql, params)
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [
            {
                'participant_response': r[0],
                'coach_response': r[1],
                'category': r[2],
                'goal_type': r[3],
                'similarity': r[4]
            }
            for r in results
        ]