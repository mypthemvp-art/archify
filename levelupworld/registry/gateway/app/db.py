"""Postgres access with per-request RLS context (app.org_id).

When DATABASE_URL is unset, operations no-op and callers use in-memory stores.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

DATABASE_URL = os.environ.get("DATABASE_URL")


class Database:
    def __init__(self, url: str | None = None):
        self.url = url if url is not None else DATABASE_URL
        self._pool = None
        if self.url:
            try:
                import psycopg

                self._psycopg = psycopg
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("psycopg is required when DATABASE_URL is set") from exc

    @property
    def enabled(self) -> bool:
        return bool(self.url)

    @contextmanager
    def session(self, *, org_id: str, actor_subject: str) -> Iterator[Any]:
        """Yield a connection with RLS GUC vars set. Caller must commit/rollback."""
        if not self.enabled:
            yield None
            return
        with self._psycopg.connect(self.url) as conn:
            with conn.cursor() as cur:
                # SET LOCAL requires a transaction block
                cur.execute("BEGIN")
                cur.execute("SELECT set_config('app.org_id', %s, true)", (org_id,))
                cur.execute("SELECT set_config('app.actor_subject', %s, true)", (actor_subject,))
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def fetchall(self, sql: str, params: tuple | dict, *, org_id: str, actor_subject: str) -> list[tuple]:
        if not self.enabled:
            return []
        with self.session(org_id=org_id, actor_subject=actor_subject) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())


db = Database()
