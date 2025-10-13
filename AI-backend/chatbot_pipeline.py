#!/usr/bin/env python3
"""
Main pipeline: Read transcripts → Setup database → Generate embeddings → Load data
Testing comments are commented out
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_requirements():
    """Check if all requirements are met before starting"""
    # print("Checking requirements...")
    
    # Check for .env file
    if not os.path.exists('.env'):
        print("ERROR: .env file not found!")
        print("Please create a .env file with your credentials")
        return False
    
    # Check for required env variables
    required_vars = ['OPENAI_API_KEY', 'DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        return False
    
    # print("✓ All requirements met\n")
    return True

def run_step(step_name, function):
    """Run a pipeline step with error handling"""
    # print("=" * 80)
    # print(f"STEP: {step_name}")
    # print("=" * 80)
    
    try:
        function()
        # print(f"✓ {step_name} completed successfully\n")
        return True
    except Exception as e:
        print(f"✗ ERROR in {step_name}: {e}")
        print(f"Pipeline stopped at: {step_name}\n")
        return False

def step1_process_transcripts():
    """Step 1: Process transcript files into CSV"""
    from parse_transcripts2 import process_all_files
    
    # print("Processing transcript files from 'transcripts' folder...")
    
    # Check if transcripts folder exists
    if not os.path.exists('transcripts'):
        print("WARNING: 'transcripts' folder not found!")
        print("Looking for existing coach_responses.csv...")
        
        if os.path.exists('coach_responses.csv'):
            print("✓ Found existing coach_responses.csv - skipping transcript processing")
            return
        else:
            raise FileNotFoundError(
                "No 'transcripts' folder and no coach_responses.csv found!\n"
                "Please either:\n"
                "  1. Create a 'transcripts' folder with your .txt files, OR\n"
                "  2. Place your coach_responses.csv in the current directory"
            )
    
    # Process transcripts
    process_all_files("transcripts")
    
    # Verify CSV was created
    if not os.path.exists('coach_responses.csv'):
        raise FileNotFoundError("coach_responses.csv was not created during processing!")
    
    # print("✓ Transcripts processed successfully")

def step2_setup_database():
    """Step 2: Create database tables and indexes"""
    from setup_database import setup_database
    from setup_database import reset_database
    
    reset_database()
    setup_database()

def step3_load_embeddings():
    """Step 3: Generate embeddings and load into database"""
    from load_embeddings import load_csv_to_database
    load_csv_to_database('coach_responses.csv')

def step4_verify_setup():
    """Step 4: Verify everything is working"""
    import psycopg2
    
    # Support both DATABASE_URL and individual params
    def get_db_connection():
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            return psycopg2.connect(database_url)
        else:
            return psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD')
            )
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check record count
    cur.execute("SELECT COUNT(*) FROM coaching_conversations")
    count = cur.fetchone()[0]
    
    # Check if embeddings exist
    cur.execute("SELECT COUNT(*) FROM coaching_conversations WHERE participant_embedding IS NOT NULL")
    embedding_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    # print(f"Total records: {count}")
    # print(f"Records with embeddings: {embedding_count}")
    
    if count == 0:
        raise Exception("No records found in database!")
    if embedding_count == 0:
        raise Exception("No embeddings found!")
    
    # print("✓ Database verification passed")

def step5_test_search():
    """Step 5: Test vector search functionality"""
    from query import VectorSearch
    
    searcher = VectorSearch()
    
    test_query = "I'm feeling stressed"
    results = searcher.search(test_query, limit=3)
    
    if not results:
        raise Exception("Search returned no results!")
    
    # print(f"Test query: '{test_query}'")
    # print(f"Found {len(results)} results")
    # print(f"Top result similarity: {results[0][4]:.3f}")
    # print("✓ Vector search is working")

def main():
    """Run the complete pipeline"""
    # print("\n" + "=" * 80)
    # print("CHATBOT DATABASE SETUP PIPELINE")
    # print("=" * 80 + "\n")
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Define pipeline steps
    steps = [
        ("Process Transcripts", step1_process_transcripts),
        ("Setup Database", step2_setup_database),
        ("Generate & Load Embeddings", step3_load_embeddings),
        ("Verify Setup", step4_verify_setup),
        ("Test Vector Search", step5_test_search)
    ]
    
    # Run each step
    for step_name, step_function in steps:
        if not run_step(step_name, step_function):
            sys.exit(1)
    
    # Success message
    # print("=" * 80)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY!")
    # print("=" * 80)
    # print("\nYour chatbot database is ready to use!")
    # print("You can now use query.py to query the database.")
    # print("\nTo test it, run: python3 query.py")

if __name__ == "__main__":
    main()