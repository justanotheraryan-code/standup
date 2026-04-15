import sqlite3
from datetime import datetime
from typing import Optional

from standup.config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    text             TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'open'
                         CHECK(status IN ('open', 'done', 'skipped')),
    source           TEXT NOT NULL DEFAULT 'manual'
                         CHECK(source IN ('manual', 'suggested')),
    inferred_project TEXT,
    suggested_date   TEXT,
    completed_at     TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status);
CREATE INDEX IF NOT EXISTS idx_todos_created ON todos(created_at);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with get_conn() as conn:
        conn.executescript(_SCHEMA)


def add_todo(
    text: str,
    source: str = "manual",
    suggested_date: Optional[str] = None,
) -> int:
    """Insert a new open todo. Returns the new row id."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO todos (text, source, suggested_date) VALUES (?, ?, ?)",
            (text, source, suggested_date),
        )
        return cur.lastrowid


def set_status(todo_id: int, status: str) -> bool:
    """
    Transition a todo's status. Sets completed_at when status='done'.
    Only transitions from 'open'. Returns True if a row was updated.
    """
    now = datetime.utcnow().isoformat() if status == "done" else None
    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE todos
            SET status = ?,
                completed_at = COALESCE(?, completed_at)
            WHERE id = ? AND status = 'open'
            """,
            (status, now, todo_id),
        )
        return cur.rowcount > 0


def set_inferred_project(todo_id: int, project: str) -> None:
    """Backfill the AI-inferred project label on an existing todo."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE todos SET inferred_project = ? WHERE id = ?",
            (project, todo_id),
        )


def get_open_todos() -> list[sqlite3.Row]:
    """All open todos, oldest first."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM todos WHERE status = 'open' ORDER BY created_at ASC"
        ).fetchall()


def get_all_todos(limit: int = 50) -> list[sqlite3.Row]:
    """All todos of any status, newest first."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM todos ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()


def get_completion_stats() -> dict:
    """
    Returns stats dict with keys:
        total, done, skipped, open,
        manual_done, suggested_done, suggested_total
    """
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*)                                                    AS total,
                SUM(CASE WHEN status='done'    THEN 1 ELSE 0 END)           AS done,
                SUM(CASE WHEN status='skipped' THEN 1 ELSE 0 END)           AS skipped,
                SUM(CASE WHEN status='open'    THEN 1 ELSE 0 END)           AS open,
                SUM(CASE WHEN status='done'  AND source='manual'    THEN 1 ELSE 0 END) AS manual_done,
                SUM(CASE WHEN status='done'  AND source='suggested' THEN 1 ELSE 0 END) AS suggested_done,
                SUM(CASE WHEN source='suggested'                    THEN 1 ELSE 0 END) AS suggested_total
            FROM todos
            """
        ).fetchone()
        return dict(row)
