import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import SQLITE_DB_PATH
from app.db.models import SCHEMA_STATEMENTS


def _ensure_parent_dir():
    Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    _ensure_parent_dir()
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)


if __name__ == "__main__":
    init_db()
    print(f"Initialized SQLite DB at {SQLITE_DB_PATH}")
