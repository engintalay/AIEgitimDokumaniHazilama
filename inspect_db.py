import sqlite3
import json

def inspect_db():
    conn = sqlite3.connect('data/database.db')
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]
    
    print(f"Veri Tabanı Analizi (data/database.db)\n" + "="*40)
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [c[1] for c in cursor.fetchall()]
        
        print(f"\n📍 Tablo: {table} ({count} kayıt)")
        print(f"   Sütunlar: {', '.join(columns)}")
        
        cursor.execute(f"SELECT * FROM {table} LIMIT 2")
        rows = cursor.fetchall()
        for i, row in enumerate(rows):
            print(f"   Kayıt {i+1}: {row}")
            
    conn.close()

if __name__ == "__main__":
    inspect_db()
