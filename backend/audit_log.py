from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlparse
import psycopg

from app.config import settings

Clock = Callable[[], datetime]
ConnectionFactory = Callable[[], Any]


def default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _sqlite_connection_factory(database_url: str) -> ConnectionFactory:
    parsed = urlparse(database_url)
    path = parsed.path or ":memory:"
    if path == "/:memory:":
        path = ":memory:"
    return lambda: sqlite3.connect(path)


def _postgres_connection_factory(database_url: str) -> ConnectionFactory:
    postgres_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return lambda: psycopg.connect(postgres_url)


def default_connection_factory() -> ConnectionFactory:
    database_url = settings.database_url
    if database_url.startswith("sqlite://"):
        return _sqlite_connection_factory(database_url)
    return _postgres_connection_factory(database_url)


def _is_sqlite_connection(connection: Any) -> bool:
    return isinstance(connection, sqlite3.Connection)


def initialize_audit_log_table(connection: Any) -> None:
    if _is_sqlite_connection(connection):
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_source TEXT NOT NULL,
                input_json TEXT NOT NULL,
                output_result TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    else:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id BIGSERIAL PRIMARY KEY,
                trigger_source TEXT NOT NULL,
                input_json TEXT NOT NULL,
                output_result TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )


class AuditLogStore:
    def __init__(
        self,
        connection_factory: ConnectionFactory,
        *,
        clock: Clock | None = None,
        close_connection: bool = True,
    ) -> None:
        self._connection_factory = connection_factory
        self._clock = clock or default_clock
        self._close_connection = close_connection

    def append(
        self,
        trigger_source: str,
        input_payload: dict[str, Any],
        output_result: dict[str, Any],
    ) -> None:
        created_at = self._clock().isoformat()
        input_json = json.dumps(input_payload, sort_keys=True)
        output_json = json.dumps(output_result, sort_keys=True)
        connection = self._connection_factory()
        try:
            initialize_audit_log_table(connection)
            if _is_sqlite_connection(connection):
                connection.execute(
                    """
                    INSERT INTO audit_log (trigger_source, input_json, output_result, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (trigger_source, input_json, output_json, created_at),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO audit_log (trigger_source, input_json, output_result, created_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (trigger_source, input_json, output_json, created_at),
                )
            connection.commit()
        finally:
            if self._close_connection:
                connection.close()


_DEFAULT_STORE: AuditLogStore | None = None


def get_default_audit_log_store() -> AuditLogStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = AuditLogStore(default_connection_factory())
    return _DEFAULT_STORE
