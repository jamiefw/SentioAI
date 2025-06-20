# backend/app/services/database.py
import sqlite3
import os
from datetime import datetime

# Define the path for your SQLite database file
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
    os.makedirs(DB_FOLDER, exist_ok=True) # Ensure the data directory exists

    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    emotion TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    prompt TEXT,
                    entry_text TEXT NOT NULL,
                    ai_response TEXT,
                    voice_data TEXT,
                    readable_time TEXT NOT NULL
                );
            """)
            conn.commit()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Database table 'journal_entries' ensured at {DB_PATH}")
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error creating tables: {e}")
        finally:
            if conn:
                conn.close()

def insert_journal_entry(entry_data):
    """
    Insert a new journal entry into the database.
    Returns True if insertion was successful, False otherwise.
    """
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO journal_entries (
                    id, timestamp, emotion, confidence, prompt, entry_text, ai_response, voice_data, readable_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                entry_data.get('id'),
                entry_data.get('timestamp'),
                entry_data.get('emotion'),
                entry_data.get('confidence'),
                entry_data.get('prompt'),
                entry_data.get('entry_text'),
                entry_data.get('ai_response'),
                entry_data.get('voice_data'),
                entry_data.get('readable_time')
            ))
            conn.commit()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Journal entry {entry_data.get('id')} inserted into DB.")
            return True
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error inserting journal entry: {e}")
            return False
        finally:
            if conn:
                conn.close()

def get_all_journal_entries():
    """Retrieve all journal entries from the database."""
    conn = create_connection()
    entries = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM journal_entries ORDER BY timestamp ASC;")
            rows = cursor.fetchall()

            col_names = [description[0] for description in cursor.description]
            for row in rows:
                entries.append(dict(zip(col_names, row)))

        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error retrieving journal entries: {e}")
        finally:
            if conn:
                conn.close()
    return entries

# Example usage (for testing this module independently if needed)
if __name__ == '__main__':
    # This block only runs if database.py is executed directly, not imported
    create_tables()
    # Example data for direct testing
    # from datetime import datetime
    # import uuid
    # test_entry = {
    #     'id': str(uuid.uuid4()),
    #     'timestamp': datetime.now().isoformat(),
    #     'emotion': 'happy',
    #     'confidence': 95.5,
    #     'prompt': 'Test prompt from direct run',
    #     'entry_text': 'This is a test entry.',
    #     'ai_response': 'AI test response.',
    #     'voice_data': '{"tone": "happy"}',
    #     'readable_time': datetime.now().strftime("%I:%M %p on %B %d, %Y")
    # }
    # insert_journal_entry(test_entry)
    # print("All entries:", get_all_journal_entries())