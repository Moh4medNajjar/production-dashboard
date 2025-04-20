import sqlite3
from datetime import datetime, timedelta
import random
from pathlib import Path

DB_PATH = Path(__file__).parent / "local_database.db"

def init_db():
    """Initialise la base de données SQLite locale"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plateaux (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        ligne INTEGER NOT NULL,
        id_operatrice TEXT NOT NULL,
        poids REAL NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

def get_db():
    """Retourne une connexion à la base de données"""
    return sqlite3.connect(DB_PATH)

def generate_test_data(days=50, records=100):
    """Génère des données de test réalistes"""
    base_date = datetime.now() - timedelta(days=days)
    conn = get_db()
    cursor = conn.cursor()
    
    for _ in range(records):
        date = base_date + timedelta(days=random.randint(0, days))
        data = (
            date.strftime("%Y-%m-%d"),
            random.randint(1, 2),
            f"OP{random.randint(1, 88):03d}",
            round(random.uniform(1.5, 2.0), 2)
        )
        
        cursor.execute(
            "INSERT INTO plateaux (date, ligne, id_operatrice, poids) VALUES (?, ?, ?, ?)",
            data
        )
    
    conn.commit()
    conn.close()
    print(f"✅ {records} enregistrements de test générés")

if __name__ == "__main__":
    init_db()
    generate_test_data()