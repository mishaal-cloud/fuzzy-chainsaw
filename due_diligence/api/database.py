"""SQLite database layer for API keys, jobs, and results."""

import sqlite3
import uuid
import hashlib
import secrets
import os
from datetime import datetime, timezone
from contextlib import contextmanager


DB_PATH = os.getenv("DD_DATABASE_PATH", os.path.join(os.path.dirname(__file__), "due_diligence.db"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                key_hash TEXT UNIQUE NOT NULL,
                key_prefix TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                tier TEXT DEFAULT 'free',
                credits_remaining INTEGER DEFAULT 5,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                api_key_id TEXT NOT NULL,
                query TEXT NOT NULL,
                status TEXT DEFAULT 'queued',
                current_stage INTEGER DEFAULT 0,
                stage_name TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                error TEXT,
                result_memo TEXT,
                result_report TEXT,
                result_infographic TEXT,
                result_summary TEXT,
                elapsed_seconds REAL,
                FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
            );

            CREATE INDEX IF NOT EXISTS idx_analyses_api_key ON analyses(api_key_id);
            CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);
            CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
        """)


# ── API Key Management ──────────────────────────────────────────────


def create_api_key(name: str, email: str = "", tier: str = "free") -> dict:
    """Generate a new API key. Returns the key (only shown once) and metadata."""
    key_id = str(uuid.uuid4())
    raw_key = f"dd_{secrets.token_urlsafe(32)}"
    key_h = hash_key(raw_key)
    prefix = raw_key[:10]

    credits_map = {"free": 5, "pro": 100, "enterprise": 10000}
    credits = credits_map.get(tier, 5)

    with get_db() as conn:
        conn.execute(
            """INSERT INTO api_keys (id, key_hash, key_prefix, name, email, tier, credits_remaining, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (key_id, key_h, prefix, name, email, tier, credits, _now()),
        )

    return {
        "id": key_id,
        "api_key": raw_key,
        "prefix": prefix,
        "name": name,
        "email": email,
        "tier": tier,
        "credits_remaining": credits,
    }


def validate_api_key(raw_key: str) -> dict | None:
    """Validate an API key. Returns key record or None."""
    key_h = hash_key(raw_key)
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1", (key_h,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
                (_now(), row["id"]),
            )
            return dict(row)
    return None


def decrement_credits(key_id: str) -> bool:
    """Decrement credits for an API key. Returns False if no credits left."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT credits_remaining, tier FROM api_keys WHERE id = ?", (key_id,)
        ).fetchone()
        if not row:
            return False
        if row["tier"] == "enterprise":
            return True  # unlimited
        if row["credits_remaining"] <= 0:
            return False
        conn.execute(
            "UPDATE api_keys SET credits_remaining = credits_remaining - 1 WHERE id = ?",
            (key_id,),
        )
        return True


def list_api_keys() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, key_prefix, name, email, tier, credits_remaining, created_at, last_used_at, is_active FROM api_keys ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def revoke_api_key(key_id: str) -> bool:
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,)
        )
        return cur.rowcount > 0


# ── Analysis Job Management ─────────────────────────────────────────


def create_analysis(api_key_id: str, query: str) -> str:
    """Create a new analysis job. Returns the analysis ID."""
    analysis_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            """INSERT INTO analyses (id, api_key_id, query, status, created_at)
               VALUES (?, ?, ?, 'queued', ?)""",
            (analysis_id, api_key_id, query, _now()),
        )
    return analysis_id


def get_analysis(analysis_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
        return dict(row) if row else None


def get_analyses_for_key(api_key_id: str, limit: int = 20) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, query, status, current_stage, stage_name, created_at, completed_at, elapsed_seconds FROM analyses WHERE api_key_id = ? ORDER BY created_at DESC LIMIT ?",
            (api_key_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def update_analysis_stage(analysis_id: str, stage: int, stage_name: str):
    with get_db() as conn:
        now = _now()
        conn.execute(
            """UPDATE analyses SET current_stage = ?, stage_name = ?, status = 'running',
               started_at = COALESCE(started_at, ?) WHERE id = ?""",
            (stage, stage_name, now, analysis_id),
        )


def complete_analysis(analysis_id: str, memo: str, report: str, infographic: str, summary: str, elapsed: float):
    with get_db() as conn:
        conn.execute(
            """UPDATE analyses SET status = 'completed', current_stage = 7, stage_name = 'Complete',
               completed_at = ?, result_memo = ?, result_report = ?, result_infographic = ?,
               result_summary = ?, elapsed_seconds = ? WHERE id = ?""",
            (_now(), memo, report, infographic, summary, elapsed, analysis_id),
        )


def fail_analysis(analysis_id: str, error: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE analyses SET status = 'failed', error = ?, completed_at = ? WHERE id = ?",
            (error, _now(), analysis_id),
        )


def get_next_queued() -> dict | None:
    """Get the next queued analysis (FIFO)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
