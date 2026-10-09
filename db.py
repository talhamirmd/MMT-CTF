import os
import sqlite3

# Postgres when DATABASE_URL is set (hosting), otherwise a local SQLite file.
DATABASE_URL = os.environ.get("DATABASE_URL", "")
IS_PG = DATABASE_URL.startswith(("postgres://", "postgresql://"))

if os.environ.get("RENDER") and not IS_PG:
    print("WARNING: DATABASE_URL is not set. Accounts and scores are stored on Render's disk, "
          "which is wiped on every restart.", flush=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    id            {id},
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    {float} NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id            {id},
    username      TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    {float} NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS users_username ON users (lower(username));
CREATE TABLE IF NOT EXISTS solves (
    id           {id},
    user_id      INTEGER NOT NULL,
    challenge_id TEXT NOT NULL,
    created_at   {float} NOT NULL,
    UNIQUE (user_id, challenge_id)
);
CREATE TABLE IF NOT EXISTS submissions (
    id           {id},
    user_id      INTEGER NOT NULL,
    challenge_id TEXT NOT NULL,
    submitted    TEXT NOT NULL,
    correct      INTEGER NOT NULL,
    created_at   {float} NOT NULL
);
CREATE TABLE IF NOT EXISTS opened (
    user_id      INTEGER NOT NULL,
    challenge_id TEXT NOT NULL,
    opened_at    {float} NOT NULL,
    PRIMARY KEY (user_id, challenge_id)
);
CREATE TABLE IF NOT EXISTS challenge_state (
    challenge_id TEXT PRIMARY KEY,
    hidden       INTEGER NOT NULL DEFAULT 0
);
"""


class Database:
    """Thin wrapper so the app can write one kind of SQL (with ? placeholders) for both databases."""

    def __init__(self, sqlite_path):
        if IS_PG:
            import psycopg
            from psycopg.rows import dict_row
            self.conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        else:
            self.conn = sqlite3.connect(sqlite_path)
            self.conn.row_factory = sqlite3.Row

    def execute(self, sql, params=()):
        if IS_PG:
            sql = sql.replace("?", "%s")
        return self.conn.execute(sql, params)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def init(sqlite_path):
    db = Database(sqlite_path)
    if not IS_PG:
        _move_old_sqlite_tables(db)
    types = {"id": "SERIAL PRIMARY KEY", "float": "DOUBLE PRECISION"} if IS_PG else \
            {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "float": "REAL"}
    for statement in SCHEMA.format(**types).split(";"):
        if statement.strip():
            db.execute(statement)
    db.commit()
    db.close()


def _move_old_sqlite_tables(db):
    # before accounts, progress was stored per anonymous browser (player_id). Keep that data
    # under another name instead of deleting it.
    for table in ("solves", "submissions"):
        cols = [r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()]
        if "player_id" in cols:
            db.execute(f"ALTER TABLE {table} RENAME TO {table}_anonymous")
