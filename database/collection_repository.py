"""
Collection Repository - SQLite data access for the mascot collection system.
SQL only, no business logic. Tables are designed so they can later be synced
with a server (transactions table acts as an append-only ledger).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from database.base_repository import BaseRepository
from utils.paths import get_database_path


class CollectionRepository(BaseRepository):

    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path or get_database_path())
        self._init_tables()

    def _init_tables(self):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS collection_wallets (
                    user_key TEXT PRIMARY KEY,
                    coins INTEGER NOT NULL DEFAULT 0,
                    shards INTEGER NOT NULL DEFAULT 0,
                    eggs INTEGER NOT NULL DEFAULT 0,
                    pity INTEGER NOT NULL DEFAULT 0,
                    last_daily TEXT,
                    streak INTEGER NOT NULL DEFAULT 0,
                    voice_day TEXT,
                    voice_coins_today INTEGER NOT NULL DEFAULT 0,
                    starter_given INTEGER NOT NULL DEFAULT 0,
                    equipped TEXT NOT NULL DEFAULT 'pop',
                    total_opened INTEGER NOT NULL DEFAULT 0
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS collection_owned (
                    user_key TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 1,
                    first_obtained TEXT NOT NULL,
                    PRIMARY KEY (user_key, character_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS collection_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    character_id TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    # ---------------- Wallet ----------------
    def get_wallet(self, user_key: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM collection_wallets WHERE user_key = ?", (user_key,))
            row = cur.fetchone()
            if row is None:
                cur.execute("INSERT INTO collection_wallets (user_key) VALUES (?)", (user_key,))
                conn.commit()
                cur.execute("SELECT * FROM collection_wallets WHERE user_key = ?", (user_key,))
                row = cur.fetchone()
            return dict(row)

    def update_wallet(self, user_key: str, **fields: Any) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self._get_connection() as conn:
            conn.execute(f"UPDATE collection_wallets SET {cols} WHERE user_key = ?",
                         (*fields.values(), user_key))
            conn.commit()

    # ---------------- Owned characters ----------------
    def get_owned(self, user_key: str) -> Dict[str, int]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT character_id, count FROM collection_owned WHERE user_key = ?", (user_key,)
            ).fetchall()
            return {r["character_id"]: r["count"] for r in rows}

    def add_owned(self, user_key: str, character_id: str) -> int:
        """Increment owned count, return new count."""
        now = datetime.now().isoformat(timespec="seconds")
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO collection_owned (user_key, character_id, count, first_obtained)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(user_key, character_id) DO UPDATE SET count = count + 1
            """, (user_key, character_id, now))
            conn.commit()
            row = conn.execute(
                "SELECT count FROM collection_owned WHERE user_key = ? AND character_id = ?",
                (user_key, character_id),
            ).fetchone()
            return int(row["count"]) if row else 1

    # ---------------- Ledger ----------------
    def log(self, user_key: str, kind: str, currency: str, amount: int,
            character_id: Optional[str] = None) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO collection_transactions (user_key, kind, currency, amount, character_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_key, kind, currency, amount, character_id, now))
            conn.commit()

    def recent_transactions(self, user_key: str, limit: int = 30) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM collection_transactions WHERE user_key = ?
                ORDER BY id DESC LIMIT ?
            """, (user_key, limit)).fetchall()
            return [dict(r) for r in rows]
