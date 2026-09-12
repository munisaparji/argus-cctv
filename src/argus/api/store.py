from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from argus.orchestrator import utc_now
from argus.schema import Annotation, DecisionRequest, IncidentRecord


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
              CREATE TABLE IF NOT EXISTS incidents(id TEXT PRIMARY KEY, record TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
              CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT, 'append-only audit'); END;
              CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT, 'append-only audit'); END;
              CREATE TABLE IF NOT EXISTS annotations(clip_id TEXT, annotator TEXT, payload TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(clip_id,annotator));
            """)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def put(self, record: IncidentRecord) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO incidents VALUES (?,?)", (record.incident_id, record.model_dump_json())
            )

    def get(self, incident_id: str) -> IncidentRecord:
        with self.connect() as db:
            row = db.execute("SELECT record FROM incidents WHERE id=?", (incident_id,)).fetchone()
        if row is None:
            raise KeyError(incident_id)
        return IncidentRecord.model_validate_json(row[0])

    def list(self) -> list[IncidentRecord]:
        with self.connect() as db:
            return [
                IncidentRecord.model_validate_json(row[0])
                for row in db.execute("SELECT record FROM incidents ORDER BY rowid DESC")
            ]

    def decide(self, incident_id: str, request: DecisionRequest) -> IncidentRecord:
        # WHY: One transaction makes the human state and immutable audit entry indivisible.
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT record FROM incidents WHERE id=?", (incident_id,)).fetchone()
            if row is None:
                raise KeyError(incident_id)
            record = IncidentRecord.model_validate_json(row[0])
            if record.human.state != "AWAITING_HUMAN_CONFIRMATION":
                raise ValueError("This incident already has a human decision")
            if not record.m7_response:
                raise ValueError("Cannot decide before policy completion")
            now = utc_now()
            payload = json.dumps(
                {
                    "timestamp": now,
                    "incident_id": incident_id,
                    "operator": request.operator,
                    "decision": request.decision,
                    "operator_note": request.note,
                    "actions": [a.value for a in record.m7_response.recommended_actions],
                },
                sort_keys=True,
            )
            previous = db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            prev_hash = previous[0] if previous else "0" * 64
            hash_value = hashlib.sha256((prev_hash + payload).encode()).hexdigest()
            db.execute(
                "INSERT INTO audit(payload,prev_hash,hash) VALUES (?,?,?)", (payload, prev_hash, hash_value)
            )
            record.human.state = "CONFIRMED" if request.decision == "confirm" else "DISMISSED"
            record.human.decision = request.decision
            record.human.operator_note = request.note
            record.human.decided_at = now
            db.execute("UPDATE incidents SET record=? WHERE id=?", (record.model_dump_json(), incident_id))
        return record

    def audit(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [
                {
                    **json.loads(row["payload"]),
                    "seq": row["seq"],
                    "hash": row["hash"],
                    "prev_hash": row["prev_hash"],
                }
                for row in db.execute("SELECT * FROM audit ORDER BY seq")
            ]

    def save_annotation(self, annotation: Annotation) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO annotations VALUES (?,?,?,?) ON CONFLICT(clip_id,annotator) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at",
                (annotation.clip_id, annotation.annotator, annotation.model_dump_json(), utc_now()),
            )

    def annotations(self, annotator: str | None = None) -> list[Annotation]:
        with self.connect() as db:
            cursor = (
                db.execute("SELECT payload FROM annotations WHERE annotator=?", (annotator,))
                if annotator
                else db.execute("SELECT payload FROM annotations")
            )
            return [Annotation.model_validate_json(row[0]) for row in cursor]
