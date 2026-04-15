import sqlite3
from datetime import date, timedelta
from typing import Optional

from standup.config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS standups (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL UNIQUE,
    yesterday   TEXT NOT NULL,
    today       TEXT NOT NULL,
    blockers    TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_standups_date ON standups(date);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with get_conn() as conn:
        conn.executescript(_SCHEMA)
    # Lazy import to avoid any circular-import risk at module load time
    from standup import todos as _todos
    _todos.init()


def upsert_standup(date_str: str, yesterday: str, today: str, blockers: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO standups (date, yesterday, today, blockers)
            VALUES (?, ?, ?, ?)
            """,
            (date_str, yesterday, today, blockers),
        )


def get_today() -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM standups WHERE date = ?",
            (date.today().isoformat(),),
        ).fetchone()
    return row


def get_week(iso_week_start: str) -> list[sqlite3.Row]:
    start = date.fromisoformat(iso_week_start)
    end = start + timedelta(days=6)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM standups WHERE date >= ? AND date <= ? ORDER BY date ASC",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
    return rows


def get_recent_standups(n: int = 14) -> list[sqlite3.Row]:
    """Return the N most recent standup entries, newest first."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM standups ORDER BY date DESC LIMIT ?",
            (n,),
        ).fetchall()


def get_all_standups() -> list[sqlite3.Row]:
    """Return all standup entries, oldest first."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM standups ORDER BY date ASC"
        ).fetchall()


def get_all_weeks() -> list[tuple[str, int]]:
    """Return list of (iso_week_string, entry_count) ordered newest first."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                strftime('%Y-W%W', date) AS week,
                COUNT(*) AS count
            FROM standups
            GROUP BY week
            ORDER BY week DESC
            """
        ).fetchall()
    return [(row["week"], row["count"]) for row in rows]
