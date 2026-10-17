"""Small SQLite JSON store. Immutable IDs survive reloads and multiple workers."""
import os
from pathlib import Path
from contextlib import contextmanager
import sqlite3
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class CapacityError(Exception):
    pass


class StorageUnavailable(Exception):
    pass


class Store(Generic[T]):
    def __init__(self, namespace: str, model: type[T]):
        self.namespace = namespace
        self.model = model

    @contextmanager
    def connection(self):
        conn = None
        try:
            path = Path(os.getenv("ARTERIA_DB_PATH", str(Path(__file__).parent / ".data" / "arteria.sqlite3")))
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(path, timeout=10)
            conn.execute("CREATE TABLE IF NOT EXISTS records (namespace TEXT, id TEXT, payload TEXT NOT NULL, PRIMARY KEY(namespace, id))")
            yield conn
        except (OSError, sqlite3.Error) as exc:
            raise StorageUnavailable("Database temporarily unavailable") from exc
        finally:
            if conn is not None:
                conn.close()

    def get(self, key: str) -> T | None:
        with self.connection() as conn:
            row = conn.execute("SELECT payload FROM records WHERE namespace=? AND id=?", (self.namespace, key)).fetchone()
            return self.model.model_validate_json(row[0]) if row else None

    def put(self, key: str, value: T, limit: int = 1000) -> T:
        with self.connection() as conn:
            with conn:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute("SELECT payload FROM records WHERE namespace=? AND id=?", (self.namespace, key)).fetchone()
                if row:
                    return self.model.model_validate_json(row[0])
                count = conn.execute("SELECT COUNT(*) FROM records WHERE namespace=?", (self.namespace,)).fetchone()[0]
                if count >= limit:
                    raise CapacityError("Storage capacity reached. Configure a fresh ARTERIA_DB_PATH or archive existing records.")
                conn.execute("INSERT INTO records VALUES (?, ?, ?)", (self.namespace, key, value.model_dump_json()))
            return value.model_copy(deep=True)

    def clear(self):
        """Used by isolated tests; no public deletion endpoint."""
        with self.connection() as conn:
            with conn:
                conn.execute("DELETE FROM records WHERE namespace=?", (self.namespace,))
