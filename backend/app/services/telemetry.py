import sqlite3
import json
from pathlib import Path

DB_PATH = Path("telemetry.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_ms INTEGER,
            validation_ms INTEGER,
            embedding_ms INTEGER,
            retrieval_ms INTEGER,
            generation_ms INTEGER,
            grounding_ms INTEGER,
            success BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

def log_metrics(latencies: dict, success: bool):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO metrics (total_ms, validation_ms, embedding_ms, retrieval_ms, generation_ms, grounding_ms, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            latencies.get("total_ms", 0),
            latencies.get("validation_ms", 0),
            latencies.get("embedding_ms", 0),
            latencies.get("retrieval_ms", 0),
            latencies.get("generation_ms", 0),
            latencies.get("grounding_ms", 0),
            success
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log metrics: {e}")

def get_historical_metrics():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 100')
        rows = cursor.fetchall()
        
        if not rows:
            return None
            
        total_ms_list = [row['total_ms'] for row in rows]
        
        # Calculate percentiles
        total_ms_list.sort()
        n = len(total_ms_list)
        
        p50 = total_ms_list[int(n * 0.5)]
        p70 = total_ms_list[int(n * 0.7)]
        p100 = total_ms_list[-1]
        average = sum(total_ms_list) / n
        fastest = total_ms_list[0]
        slowest = p100
        
        # Averages for stages
        avg_validation = sum(row['validation_ms'] for row in rows) / n
        avg_embedding = sum(row['embedding_ms'] for row in rows) / n
        avg_retrieval = sum(row['retrieval_ms'] for row in rows) / n
        avg_generation = sum(row['generation_ms'] for row in rows) / n
        avg_grounding = sum(row['grounding_ms'] for row in rows) / n
        
        return {
            "P50": p50,
            "P70": p70,
            "P100": p100,
            "average": int(average),
            "fastest": fastest,
            "slowest": slowest,
            "stages": {
                "validation": int(avg_validation),
                "embedding": int(avg_embedding),
                "retrieval": int(avg_retrieval),
                "generation": int(avg_generation),
                "grounding": int(avg_grounding)
            }
        }
    except Exception as e:
        print(f"Failed to get metrics: {e}")
        return None

# Initialize on import
init_db()
