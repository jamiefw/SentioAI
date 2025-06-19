import sqlite3
import os
from datetime import datetime

#defining the path for SQLite database file
DB_FOLDER = 'data'
DB_NAME = 'sentio_journal.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

def create_connection():
    """Create a database connection to the SQLite database specified by DB_PATH."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
    return conn

def create_tables():
    """Create necessary tables in the database if they don't exist."""
    os.makedirs(DB_FOLDER, exist_ok=True)

    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Table to store journal entries
            # id: Unique identifier (UUID for flexibility)
            # timestamp: ISO formatted timestamp for sorting
            # emotion: Detected emotion (e.g., 'happy', 'sad')
            # confidence: Confidence score for the emotion
            # prompt: The prompt used for the entry
            # entry_text: The user's journal entry text
            # ai_response: The AI's response text (nullable)
            # voice_data: Placeholder for future voice analysis metadata (nullable)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    emotion TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    prompt TEXT,
                    entry_text TEXT NOT NULL,
                    ai_response TEXT,
                    voice_data TEXT
                );
            """)
            conn.commit()
            print(f"Database table 'journal_entries' ensured at {DB_PATH}")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()

def insert_journal_entry(entry_data):
    """
    Insert a new journal entry into the database.

    Args:
        entry_data (dict): A dictionary containing entry details:
            - 'id': Unique ID for the entry
            - 'timestamp': ISO formatted timestamp
            - 'emotion': Detected emotion
            - 'confidence': Confidence score
            - 'prompt': Journaling prompt
            - 'entry_text': User's journal text
            - 'ai_response': AI's response (optional)
            - 'voice_data': Voice analysis data (optional)
    Returns:
        bool: True if insertion was successful, False otherwise.
    """
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO journal_entries (
                    id, timestamp, emotion, confidence, prompt, entry_text, ai_response, voice_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                entry_data.get('id'),
                entry_data.get('timestamp'),
                entry_data.get('emotion'),
                entry_data.get('confidence'),
                entry_data.get('prompt'),
                entry_data.get('entry_text'),
                entry_data.get('ai_response'),
                entry_data.get('voice_data') # This will be None if not provided
            ))
            conn.commit()
            print(f"Journal entry {entry_data.get('id')} inserted into DB.")
            return True
        except sqlite3.Error as e:
            print(f"Error inserting journal entry: {e}")
            return False
        finally:
            conn.close()

#can add more functions here later, e.g., to query data for analytics
def get_all_journal_entries():
    """Retrieve all journal entries from the database."""
    conn = create_connection()
    entries = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM journal_entries ORDER BY timestamp ASC;")
            rows = cursor.fetchall()
            
            # Get column names to create dicts for easier access
            col_names = [description[0] for description in cursor.description]
            for row in rows:
                entries.append(dict(zip(col_names, row)))
            
        except sqlite3.Error as e:
            print(f"Error retrieving journal entries: {e}")
        finally:
            conn.close()
    return entries

if __name__ == '__main__':
    create_tables()
    # Test insertion example 
    # test_entry = {
    #     'id': str(uuid.uuid4()),
    #     'timestamp': datetime.now().isoformat(),
    #     'emotion': 'happy',
    #     'confidence': 95.5,
    #     'prompt': 'What made you smile today?',
    #     'entry_text': 'I finished setting up the database!',
    #     'ai_response': 'That sounds like a great accomplishment!',
    #     'voice_data': None
    # }
    # if insert_journal_entry(test_entry):
    #     print("Test entry inserted successfully.")
    # all_entries = get_all_journal_entries()
    # print(f"Total entries in DB: {len(all_entries)}")
    # for entry in all_entries:
    #     print(entry['emotion'], entry['entry_text'])