import os
import json
import sqlite3

class TaskAuditDB:
    def __init__(self):
        self.db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
        self.local_db_file = os.path.join(os.path.dirname(__file__), "audit_history.db")
        self._init_sqlite()

    def _init_sqlite(self):
        conn = sqlite3.connect(self.local_db_file)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT,
                score INTEGER,
                passed_checks INTEGER,
                failed_checks INTEGER,
                warning_checks INTEGER,
                summary TEXT,
                audit_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_audit(self, audit_results):
        try:
            conn = sqlite3.connect(self.local_db_file)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (task_name, score, passed_checks, failed_checks, warning_checks, summary, audit_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_results.get("task_name", "unknown"),
                audit_results.get("score", 0),
                audit_results.get("passed_checks", 0),
                audit_results.get("failed_checks", 0),
                audit_results.get("warning_checks", 0),
                audit_results.get("summary", ""),
                json.dumps(audit_results)
            ))
            conn.commit()
            record_id = cursor.lastrowid
            conn.close()
            return record_id
        except Exception as e:
            print(f"DB Save Error: {e}")
            return None

    def get_recent_audits(self, limit=10):
        try:
            conn = sqlite3.connect(self.local_db_file)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, task_name, score, passed_checks, failed_checks, warning_checks, summary, created_at
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    "id": row[0],
                    "task_name": row[1],
                    "score": row[2],
                    "passed_checks": row[3],
                    "failed_checks": row[4],
                    "warning_checks": row[5],
                    "summary": row[6],
                    "created_at": row[7]
                })
            return history
        except Exception as e:
            print(f"DB Read Error: {e}")
            return []
