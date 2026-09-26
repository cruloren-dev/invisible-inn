"""SQLite storage for game sessions.

Uses Python's built-in ``sqlite3`` module. Each call runs in a worker thread
(``asyncio.to_thread``) so the bot never blocks while the disk is busy.

Schema changes go in ``MIGRATIONS``: append a new SQL string, never edit an old
one. The database remembers how many have been applied (``PRAGMA user_version``).

Group play: every session has a list of players in ``session_players``. Solo
games simply have one player (the owner). Inviting more players later only
needs new commands, not a database redesign.
"""

from __future__ import annotations

import asyncio
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .engine import GameState

MIGRATIONS: list[str] = [
    # 1 — initial schema
    """
    CREATE TABLE sessions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id    INTEGER NOT NULL,
        channel_id  INTEGER NOT NULL,          -- channel the thread was created in
        thread_id   INTEGER UNIQUE,            -- the game's private thread
        owner_id    INTEGER NOT NULL,          -- user who ran /start
        story_id    TEXT    NOT NULL,
        state       TEXT    NOT NULL,          -- GameState as JSON
        status      TEXT    NOT NULL DEFAULT 'active',  -- active | finished | abandoned
        created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX idx_sessions_status ON sessions (guild_id, status);

    CREATE TABLE session_players (
        session_id  INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        user_id     INTEGER NOT NULL,
        role        TEXT    NOT NULL DEFAULT 'player',  -- owner | player
        joined_at   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (session_id, user_id)
    );
    CREATE INDEX idx_players_user ON session_players (user_id);
    """,
]

ACTIVE, FINISHED, ABANDONED = "active", "finished", "abandoned"


@dataclass(frozen=True)
class Session:
    id: int
    guild_id: int
    channel_id: int
    thread_id: int | None
    owner_id: int
    story_id: str
    state: GameState
    status: str


def _row_to_session(row: sqlite3.Row | None) -> Session | None:
    if row is None:
        return None
    return Session(
        id=row["id"], guild_id=row["guild_id"], channel_id=row["channel_id"],
        thread_id=row["thread_id"], owner_id=row["owner_id"], story_id=row["story_id"],
        state=GameState.from_json(row["state"]), status=row["status"],
    )


class Storage:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    # -- plumbing ---------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _migrate(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            for i, sql in enumerate(MIGRATIONS[version:], start=version + 1):
                with conn:
                    conn.executescript(sql)
                    conn.execute(f"PRAGMA user_version = {i}")

    async def setup(self) -> None:
        await asyncio.to_thread(self._migrate)

    # -- sessions ---------------------------------------------------------
    def _create_session(self, guild_id, channel_id, thread_id, owner_id, story_id, state) -> Session:
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO sessions (guild_id, channel_id, thread_id, owner_id, story_id, state)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (guild_id, channel_id, thread_id, owner_id, story_id, state.to_json()),
            )
            session_id = cur.lastrowid
            conn.execute(
                "INSERT INTO session_players (session_id, user_id, role) VALUES (?, ?, 'owner')",
                (session_id, owner_id),
            )
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return _row_to_session(row)

    async def create_session(
        self, *, guild_id: int, channel_id: int, thread_id: int | None,
        owner_id: int, story_id: str, state: GameState,
    ) -> Session:
        return await asyncio.to_thread(
            self._create_session, guild_id, channel_id, thread_id, owner_id, story_id, state,
        )

    def _fetch_one(self, sql: str, params: tuple) -> Session | None:
        with closing(self._connect()) as conn:
            return _row_to_session(conn.execute(sql, params).fetchone())

    async def get_session(self, session_id: int) -> Session | None:
        return await asyncio.to_thread(self._fetch_one, "SELECT * FROM sessions WHERE id = ?", (session_id,))

    async def get_session_by_thread(self, thread_id: int) -> Session | None:
        return await asyncio.to_thread(
            self._fetch_one, "SELECT * FROM sessions WHERE thread_id = ?", (thread_id,),
        )

    async def active_session_for_user(self, guild_id: int, user_id: int) -> Session | None:
        """The user's current active game in this server, if any."""
        return await asyncio.to_thread(
            self._fetch_one,
            "SELECT s.* FROM sessions s JOIN session_players p ON p.session_id = s.id"
            " WHERE s.guild_id = ? AND p.user_id = ? AND s.status = 'active'"
            " ORDER BY s.id DESC LIMIT 1",
            (guild_id, user_id),
        )

    def _save_state(self, session_id: int, state: GameState, status: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE sessions SET state = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (state.to_json(), status, session_id),
            )

    async def save_state(self, session_id: int, state: GameState, status: str = ACTIVE) -> None:
        await asyncio.to_thread(self._save_state, session_id, state, status)

    def _set_status(self, session_id: int, status: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE sessions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, session_id),
            )

    async def set_status(self, session_id: int, status: str) -> None:
        await asyncio.to_thread(self._set_status, session_id, status)

    # -- players ----------------------------------------------------------
    def _is_player(self, session_id: int, user_id: int) -> bool:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT 1 FROM session_players WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
        return row is not None

    async def is_player(self, session_id: int, user_id: int) -> bool:
        return await asyncio.to_thread(self._is_player, session_id, user_id)

    def _add_player(self, session_id: int, user_id: int, role: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT OR IGNORE INTO session_players (session_id, user_id, role) VALUES (?, ?, ?)",
                (session_id, user_id, role),
            )

    async def add_player(self, session_id: int, user_id: int, role: str = "player") -> None:
        """For future group play (e.g. an /invite command)."""
        await asyncio.to_thread(self._add_player, session_id, user_id, role)
