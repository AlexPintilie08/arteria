"""Atomic idempotency claims and immutable storage for planning responses."""

from __future__ import annotations

import hashlib

from backend.ai_planning_models import AIPlanningResult
from backend.storage import CapacityError, Store, StorageUnavailable


class PlanningRepository:
    def __init__(self):
        self.results = Store("spatial-planning-v1", AIPlanningResult)

    @staticmethod
    def idempotency_id(study_id: str, key: str) -> str:
        return hashlib.sha256((study_id + "\0" + key).encode("utf-8")).hexdigest()

    def claim(self, scoped_key: str, planning_id: str, limit: int = 1000) -> tuple[str, str]:
        try:
            with self.results.connection() as conn:
                with conn:
                    conn.execute("BEGIN IMMEDIATE")
                    conn.execute(
                        "CREATE TABLE IF NOT EXISTS planning_idempotency "
                        "(key_hash TEXT PRIMARY KEY, planning_id TEXT NOT NULL, state TEXT NOT NULL)"
                    )
                    row = conn.execute(
                        "SELECT planning_id, state FROM planning_idempotency WHERE key_hash=?",
                        (scoped_key,),
                    ).fetchone()
                    if row:
                        return row[1], row[0]
                    result_count = conn.execute(
                        "SELECT COUNT(*) FROM records WHERE namespace=?", (self.results.namespace,)
                    ).fetchone()[0]
                    claim_count = conn.execute("SELECT COUNT(*) FROM planning_idempotency").fetchone()[0]
                    if result_count >= limit or claim_count >= limit:
                        raise CapacityError("Planning result capacity reached. Configure a fresh ARTERIA_DB_PATH or archive existing records.")
                    conn.execute(
                        "INSERT INTO planning_idempotency (key_hash, planning_id, state) VALUES (?, ?, 'pending')",
                        (scoped_key, planning_id),
                    )
            return "claimed", planning_id
        except (CapacityError, StorageUnavailable):
            raise
        except Exception as exc:
            raise StorageUnavailable("Database temporarily unavailable") from exc

    def persist_claimed(self, scoped_key: str, value: AIPlanningResult, limit: int = 1000) -> AIPlanningResult:
        try:
            with self.results.connection() as conn:
                with conn:
                    conn.execute("BEGIN IMMEDIATE")
                    row = conn.execute(
                        "SELECT planning_id, state FROM planning_idempotency WHERE key_hash=?",
                        (scoped_key,),
                    ).fetchone()
                    if not row or row[0] != value.planning_id or row[1] != "pending":
                        raise StorageUnavailable("Planning result reservation was lost")
                    existing = conn.execute(
                        "SELECT payload FROM records WHERE namespace=? AND id=?",
                        (self.results.namespace, value.planning_id),
                    ).fetchone()
                    if existing:
                        saved = AIPlanningResult.model_validate_json(existing[0])
                    else:
                        count = conn.execute(
                            "SELECT COUNT(*) FROM records WHERE namespace=?", (self.results.namespace,)
                        ).fetchone()[0]
                        if count >= limit:
                            raise CapacityError("Planning result capacity reached. Configure a fresh ARTERIA_DB_PATH or archive existing records.")
                        conn.execute(
                            "INSERT INTO records VALUES (?, ?, ?)",
                            (self.results.namespace, value.planning_id, value.model_dump_json()),
                        )
                        saved = value.model_copy(deep=True)
                    conn.execute(
                        "UPDATE planning_idempotency SET state='complete' WHERE key_hash=? AND state='pending'",
                        (scoped_key,),
                    )
            return saved
        except (CapacityError, StorageUnavailable):
            raise
        except Exception as exc:
            raise StorageUnavailable("Database temporarily unavailable") from exc

    def save(self, value: AIPlanningResult, limit: int = 1000) -> AIPlanningResult:
        return self.results.put(value.planning_id, value, limit)

    def get(self, planning_id: str) -> AIPlanningResult | None:
        return self.results.get(planning_id)


planning_results = PlanningRepository()
