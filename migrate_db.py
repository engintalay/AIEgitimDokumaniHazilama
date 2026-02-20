import sqlite3
import os

db_path = os.path.abspath('data/database.db')
print(f"Migrating database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column, type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type}")
        print(f"Added column {column} to table {table}")
    except sqlite3.OperationalError as e:
        print(f"Skipping {column} for {table}: {e}")

# Message table updates
add_column('message', 'response_time', 'REAL')
add_column('message', 'prompt_tokens', 'INTEGER')
add_column('message', 'completion_tokens', 'INTEGER')

# Report table updates (including creating the table if it doesn't exist)
try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS report (
        id INTEGER NOT NULL, 
        user_id INTEGER NOT NULL, 
        message_id INTEGER, 
        content TEXT NOT NULL, 
        image_path VARCHAR(255), 
        status VARCHAR(20), 
        timestamp DATETIME, 
        PRIMARY KEY (id), 
        FOREIGN KEY(user_id) REFERENCES user (id), 
        FOREIGN KEY(message_id) REFERENCES message (id)
    )
    """)
    print("Checked/Created report table")
except Exception as e:
    print(f"Report table error: {e}")

add_column('report', 'image_path', 'VARCHAR(255)')

conn.commit()
conn.close()
print("Migration completed.")
