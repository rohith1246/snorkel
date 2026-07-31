import os
import sqlite3
import json
import psycopg2

class TaskAuditDB:
    def __init__(self):
        self.db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
        self.use_sqlite = True
        self.sqlite_file = "audit_history.db"

        if self.db_url:
            try:
                conn = psycopg2.connect(self.db_url)
                conn.close()
                self.use_sqlite = False
                print("TaskAuditDB: Successfully connected to Neon PostgreSQL Database!")
            except Exception as e:
                print(f"TaskAuditDB: Neon DB connection error: {str(e)}. Falling back to SQLite.")

        self._init_db()

    def _get_connection(self):
        if self.use_sqlite:
            return sqlite3.connect(self.sqlite_file)
        else:
            return psycopg2.connect(self.db_url)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.use_sqlite:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT,
                    score INTEGER,
                    passed_checks INTEGER,
                    failed_checks INTEGER,
                    warning_checks INTEGER,
                    summary TEXT,
                    full_report_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS claimed_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT UNIQUE NOT NULL,
                    claimed_by TEXT DEFAULT 'Anonymous',
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    task_name VARCHAR(255),
                    score INTEGER,
                    passed_checks INTEGER,
                    failed_checks INTEGER,
                    warning_checks INTEGER,
                    summary TEXT,
                    full_report_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS claimed_tasks (
                    id SERIAL PRIMARY KEY,
                    task_name VARCHAR(255) UNIQUE NOT NULL,
                    claimed_by VARCHAR(255) DEFAULT 'Anonymous',
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

        conn.commit()
        conn.close()

    def save_audit(self, audit_results):
        conn = self._get_connection()
        cursor = conn.cursor()

        task_name = audit_results.get("task_name", "unknown")
        score = audit_results.get("score", 0)
        passed_checks = audit_results.get("passed_checks", 0)
        failed_checks = audit_results.get("failed_checks", 0)
        warning_checks = audit_results.get("warning_checks", 0)
        summary = audit_results.get("summary", "")
        full_json = json.dumps(audit_results)

        if self.use_sqlite:
            cursor.execute("""
                INSERT INTO audit_logs (task_name, score, passed_checks, failed_checks, warning_checks, summary, full_report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_name, score, passed_checks, failed_checks, warning_checks, summary, full_json))
            audit_id = cursor.lastrowid
        else:
            cursor.execute("""
                INSERT INTO audit_logs (task_name, score, passed_checks, failed_checks, warning_checks, summary, full_report_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (task_name, score, passed_checks, failed_checks, warning_checks, summary, full_json))
            audit_id = cursor.fetchone()[0]

        conn.commit()
        conn.close()
        return audit_id

    def get_recent_audits(self, limit=10):
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.use_sqlite:
            cursor.execute("SELECT id, task_name, score, passed_checks, failed_checks, warning_checks, summary, created_at FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
        else:
            cursor.execute("SELECT id, task_name, score, passed_checks, failed_checks, warning_checks, summary, created_at FROM audit_logs ORDER BY id DESC LIMIT %s", (limit,))

        rows = cursor.fetchall()
        conn.close()

        logs = []
        for r in rows:
            logs.append({
                "id": r[0],
                "task_name": r[1],
                "score": r[2],
                "passed_checks": r[3],
                "failed_checks": r[4],
                "warning_checks": r[5],
                "summary": r[6],
                "created_at": str(r[7])
            })
        return logs

    # --- CLAIM TASK METHODS ---
    def claim_task(self, task_name, claimed_by="Anonymous"):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if self.use_sqlite:
                cursor.execute("""
                    INSERT OR REPLACE INTO claimed_tasks (task_name, claimed_by)
                    VALUES (?, ?)
                """, (task_name, claimed_by))
            else:
                cursor.execute("""
                    INSERT INTO claimed_tasks (task_name, claimed_by)
                    VALUES (%s, %s)
                    ON CONFLICT (task_name) DO UPDATE SET claimed_by = EXCLUDED.claimed_by, claimed_at = CURRENT_TIMESTAMP
                """, (task_name, claimed_by))
            conn.commit()
            return True
        finally:
            conn.close()

    def unclaim_task(self, task_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if self.use_sqlite:
                cursor.execute("DELETE FROM claimed_tasks WHERE task_name = ?", (task_name,))
            else:
                cursor.execute("DELETE FROM claimed_tasks WHERE task_name = %s", (task_name,))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_claimed_tasks_dict(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT task_name, claimed_by, claimed_at FROM claimed_tasks")
            rows = cursor.fetchall()
            result = {}
            for r in rows:
                result[r[0]] = {"claimed_by": r[1], "claimed_at": str(r[2])}
            return result
        finally:
            conn.close()
