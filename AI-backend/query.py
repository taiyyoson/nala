from openai import OpenAI
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VectorSearch:
    """Vector search module for coaching conversations database"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'chatbot_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
    
    def search(self, query, limit=3, min_similarity=0.4, category_filter=None):
        """
        Search for relevant coaching conversations
        
        Args:
            query (str): User's search query
            limit (int): Maximum number of results to return
            min_similarity (float): Minimum similarity score (0-1)
            category_filter (str): Optional category to filter by
            
        Returns:
            list: List of tuples (participant_response, coach_response, 
                  context_category, goal_type, similarity_score)
        """
        
        # Generate embedding for query
        query_embedding = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding
        
        # Connect to database
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        # Build query
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
        
        # Add optional category filter
        if category_filter:
            sql += " AND context_category = %s"
            params.append(category_filter)
        
        sql += """
            ORDER BY participant_embedding <=> %s::vector
            LIMIT %s
        """
        params.extend([query_embedding, limit])
        
        # Execute query
        cur.execute(sql, params)
        results = cur.fetchall()
        
        # Cleanup
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
    
    def search_with_details(self, query, limit=3, min_similarity=0.4):
        """
        Returns results as list of dictionaries for easier access
        
        Returns:
            list: List of dicts with keys: participant_response, coach_response,
                  category, goal_type, similarity
        """
        results = self.search(query, limit, min_similarity)
        
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