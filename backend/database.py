"""
SQLite-backed session store for Compass.
Uses aiosqlite for async I/O so it doesn't block the FastAPI event loop.
Falls back gracefully to in-memory only if the DB file can't be opened.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("COMPASS_DB_PATH", "./data/compass.db")


class SessionStore:
    """
    Thin persistence layer around an in-memory session dict.

    Sessions are Python dicts with the shape used by CompassOrchestrator:
        {
            "session_id": str,
            "messages": list[dict],         # Bedrock conversation history
            "user_profile": dict,
            "eligible_programs": list,
            "local_resources": list,
            "action_plan": dict | None,
            "document_analysis": dict | None,
        }
    """

    def __init__(self) -> None:
        self._cache: dict[str, dict] = {}
        self._db_path = DB_PATH
        self._db_available = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def init_db(self) -> None:
        """Create DB file and tables. Call once at application startup."""
        try:
            os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        user_profile TEXT NOT NULL DEFAULT '{}',
                        eligible_programs TEXT NOT NULL DEFAULT '[]',
                        local_resources TEXT NOT NULL DEFAULT '[]',
                        action_plan TEXT,
                        document_analysis TEXT
                    )
                    """
                )
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                await db.commit()
            self._db_available = True
            logger.info("SessionStore: database ready at %s", self._db_path)
        except Exception as exc:
            logger.warning(
                "SessionStore: could not open SQLite DB (%s) — using in-memory only", exc
            )
            self._db_available = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_or_create_session(self, session_id: Optional[str] = None) -> dict:
        """
        Return an existing session or create a new one.

        Lookup order: in-memory cache → SQLite → create new.
        """
        sid = session_id or str(uuid4())

        # 1. Memory cache hit
        if sid in self._cache:
            return self._cache[sid]

        # 2. SQLite lookup
        if self._db_available:
            session = await self._load_from_db(sid)
            if session:
                self._cache[sid] = session
                return session

        # 3. Create new
        session = _empty_session(sid)
        self._cache[sid] = session
        return session

    async def save_session(self, session: dict) -> None:
        """Persist session state (non-blocking; errors are logged, not raised)."""
        sid = session.get("session_id")
        if not sid:
            return

        self._cache[sid] = session

        if not self._db_available:
            return

        try:
            await self._save_to_db(session)
        except Exception as exc:
            logger.warning("SessionStore: failed to persist session %s: %s", sid, exc)

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Return session or None if not found."""
        if session_id in self._cache:
            return self._cache[session_id]
        if self._db_available:
            session = await self._load_from_db(session_id)
            if session:
                self._cache[session_id] = session
                return session
        return None

    async def clear_session(self, session_id: str) -> None:
        """Delete session from memory and DB."""
        self._cache.pop(session_id, None)
        if not self._db_available:
            return
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                await db.commit()
        except Exception as exc:
            logger.warning("SessionStore: failed to clear session %s: %s", session_id, exc)

    def list_sessions(self) -> list[str]:
        """Return all session IDs currently in the memory cache."""
        return list(self._cache.keys())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_from_db(self, session_id: str) -> Optional[dict]:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                db.row_factory = aiosqlite.Row

                # Load session row
                async with db.execute(
                    "SELECT * FROM sessions WHERE id = ?", (session_id,)
                ) as cursor:
                    row = await cursor.fetchone()

                if not row:
                    return None

                session = _empty_session(session_id)
                session["user_profile"] = json.loads(row["user_profile"] or "{}")
                session["eligible_programs"] = json.loads(row["eligible_programs"] or "[]")
                session["local_resources"] = json.loads(row["local_resources"] or "[]")
                session["action_plan"] = (
                    json.loads(row["action_plan"]) if row["action_plan"] else None
                )
                session["document_analysis"] = (
                    json.loads(row["document_analysis"]) if row["document_analysis"] else None
                )

                # Load messages
                async with db.execute(
                    "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
                    (session_id,),
                ) as cursor:
                    rows = await cursor.fetchall()

                session["messages"] = [
                    {"role": r["role"], "content": json.loads(r["content"])} for r in rows
                ]

                return session
        except Exception as exc:
            logger.warning("SessionStore: DB load error for %s: %s", session_id, exc)
            return None

    async def _save_to_db(self, session: dict) -> None:
        sid = session["session_id"]
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO sessions (id, created_at, user_profile, eligible_programs,
                                      local_resources, action_plan, document_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_profile       = excluded.user_profile,
                    eligible_programs  = excluded.eligible_programs,
                    local_resources    = excluded.local_resources,
                    action_plan        = excluded.action_plan,
                    document_analysis  = excluded.document_analysis
                """,
                (
                    sid,
                    datetime.utcnow().isoformat(),
                    json.dumps(session.get("user_profile", {})),
                    json.dumps(session.get("eligible_programs", [])),
                    json.dumps(session.get("local_resources", [])),
                    json.dumps(session["action_plan"]) if session.get("action_plan") else None,
                    (
                        json.dumps(session["document_analysis"])
                        if session.get("document_analysis")
                        else None
                    ),
                ),
            )

            # Replace all messages for this session
            await db.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
            for msg in session.get("messages", []):
                await db.execute(
                    "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                    (sid, msg["role"], json.dumps(msg["content"]), datetime.utcnow().isoformat()),
                )

            await db.commit()


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _empty_session(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "messages": [],
        "user_profile": {},
        "eligible_programs": [],
        "local_resources": [],
        "action_plan": None,
        "document_analysis": None,
    }
