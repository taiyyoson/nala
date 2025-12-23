import pandas as pd
from openai import OpenAI
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
from time import sleep

# Load environment variables
load_dotenv()

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def prepare_text_for_embedding(participant_response, coach_response, context_category, goal_type):
    """
    Combine multiple fields to create richer embeddings
    This gives the model more context to understand the conversation
    """
    # Clean empty values
    context = context_category if context_category else "general"
    goal = goal_type if goal_type else "general"
    
    # Combine participant response with metadata for better context
    enhanced_text = f"Context: {context} | Goal: {goal} | {participant_response}"
    
    return enhanced_text

def prepare_coach_context(coach_response, context_category, goal_type):
    """Add context to coach responses too"""
    context = context_category if context_category else "general"
    goal = goal_type if goal_type else "general"
    
    enhanced_text = f"Context: {context} | Goal: {goal} | {coach_response}"
    
    return enhanced_text

# Database config
def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        return psycopg2.connect(database_url)
    else:
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'chatbot_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD')
        )

def get_embeddings_batch(texts, batch_size=100):
    """Generate embeddings in batches for efficiency"""
    embeddings = []
    total = len(texts)
    
    for i in range(0, total, batch_size):
        batch = texts[i:i+batch_size]
        # print(f"Processing embeddings {i+1}-{min(i+batch_size, total)} of {total}...")
        
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=batch
            )
            embeddings.extend([item.embedding for item in response.data])
            sleep(0.2)  # Rate limiting
        except Exception as e:
            print(f"Error processing batch {i}: {e}")
            raise
    
    return embeddings

def load_csv_to_database(csv_path):
    """Load CSV data, generate embeddings, and store in PostgreSQL"""
    
    print(f"Loading CSV from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows")
    
    # Clean data
    df = df.fillna('')
    
    # === NEW: Prepare enhanced texts for better embeddings ===
    print("\nPreparing enhanced text for embeddings...")
    participant_enhanced = []
    coach_enhanced = []
    
    for _, row in df.iterrows():
        # Enhance participant text
        p_text = prepare_text_for_embedding(
            row['participant_response'],
            row['coach_response'],
            row['context_category'],
            row['goal_type']
        )
        participant_enhanced.append(p_text)
        
        # Enhance coach text
        c_text = prepare_coach_context(
            row['coach_response'],
            row['context_category'],
            row['goal_type']
        )
        coach_enhanced.append(c_text)
    
    # Load embedding with enhanced text 
    print("\nGenerating embeddings for participant responses...")
    participant_embeddings = get_embeddings_batch(participant_enhanced)
    
    print("\nGenerating embeddings for coach responses...")
    coach_embeddings = get_embeddings_batch(coach_enhanced)
    
    print("\nPreparing data for database insertion...")
    data_to_insert = []
    for idx, row in df.iterrows():
        data_to_insert.append((
            row['participant_response'],
            row['coach_response'],
            row['context_category'],
            row['goal_type'],
            int(row['confidence_level']) if row['confidence_level'] else None,
            row['keywords'],
            row['source_file'],
            participant_embeddings[idx],
            coach_embeddings[idx]
        ))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Inserting data into database...")
    execute_values(cur, """
        INSERT INTO coaching_conversations 
        (participant_response, coach_response, context_category, goal_type, 
         confidence_level, keywords, source_file, participant_embedding, coach_embedding)
        VALUES %s
    """, data_to_insert)
    
    conn.commit()
    
    cur.execute("SELECT COUNT(*) FROM coaching_conversations")
    count = cur.fetchone()[0]
    print(f"\n✅ Success! Inserted {len(data_to_insert)} records.")
    print(f"Total records in database: {count}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    # Update this path to your CSV file
    csv_path = "coach_responses.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        print("Please update the csv_path variable with the correct path to your CSV file")
    else:
        load_csv_to_database(csv_path)