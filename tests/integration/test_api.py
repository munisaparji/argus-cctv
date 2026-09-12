import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from argus.api import app as api_module
from argus.api.store import Store
from argus.config import ROOT
from argus.schema import IncidentRecord


@pytest.fixture
def client(tmp_path, monkeypatch):
    store = Store(tmp_path / "test.sqlite")
    record = IncidentRecord.model_validate(json.loads((ROOT / "data/sample/incidents.json").read_text())[0])
    store.put(record)
    monkeypatch.setattr(api_module, "store", store)
    with TestClient(api_module.app) as client:
        yield client, store, record


def test_atomic_human_review(client):
    c, store, record = client
    endpoint = f"/api/incidents/{record.incident_id}/decision"
    assert c.post(endpoint, json={"decision": "dismiss", "operator": "test", "note": ""}).status_code == 422
    assert not store.audit()
    response = c.post(endpoint, json={"decision": "confirm", "operator": "test", "note": "Reviewed"})
    assert response.status_code == 200
    assert response.json()["human"]["state"] == "CONFIRMED"
    assert len(store.audit()) == 1
    assert c.post(endpoint, json={"decision": "confirm", "operator": "test"}).status_code == 409
    with store.connect() as db, pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM audit")


def test_guard_and_paths(client):
    c, _, _ = client
    assert c.get("/api/health").status_code == 200
    assert c.get("/api/incidents/unknown").status_code == 404
    assert c.get("/api/media/docs/RESULTS.md").status_code == 404
    assert (
        c.post(
            "/api/incidents/x/decision", json={}, headers={"Origin": "https://untrusted.example"}
        ).status_code
        == 403
    )


def test_registered_research_video_preview(client, tmp_path):
    c, store, record = client
    video = tmp_path / "registered.mp4"
    preview = video.with_suffix(".webm")
    video.write_bytes(b"analysis video")
    preview.write_bytes(b"browser preview")
    record.incident_id = "registered-video-test"
    record.source.video_path = video.as_posix()
    record.source.sample = False
    store.put(record)
    response = c.get("/api/media/" + video.as_posix())
    assert response.status_code == 200
    assert response.content == b"browser preview"
    other = tmp_path / "unregistered.mp4"
    other.write_bytes(b"unregistered data")
    assert c.get("/api/media/" + other.as_posix()).status_code == 404


def test_annotation_validation_and_independence(client):
    from argus.config import read_config

    c, _, record = client
    body = {
        "clip_id": record.source.clip_id,
        "annotator": "a",
        "score": 30,
        "factors": {n: 0 for n in read_config("severity_factors.yaml")["factors"]},
        "actions": ["log_only"],
        "spans": [{"start_s": 0, "end_s": 2, "label": "person"}],
        "complete": True,
    }
    assert c.put("/api/annotations", json=body).status_code == 200
    assert len(c.get("/api/annotations?annotator=a").json()) == 1
    assert c.get("/api/annotations?annotator=b").json() == []
    body["spans"][0]["end_s"] = 999
    assert c.put("/api/annotations", json=body).status_code == 422


def test_socket_trace(client):
    c, store, record = client
    with c.websocket_connect(f"/api/runs/{record.source.clip_id}") as ws:
        events = []
        while True:
            event = ws.receive_json()
            events.append(event)
            if event["status"] in {"finished", "error"}:
                break
    assert events[-1]["status"] == "finished"
    assert len([e for e in events if e["status"] == "complete"]) == 7
    assert events[-1]["record"]["human"]["state"] == "AWAITING_HUMAN_CONFIRMATION"
