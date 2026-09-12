from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from argus.api.store import Store
from argus.config import ROOT, read_config
from argus.data.sample import load_sources
from argus.orchestrator import run
from argus.schema import Action, Annotation, DecisionRequest, IncidentRecord

app = FastAPI(
    title="ARGUS",
    version="1.0.0",
    description="Offline evidence verification research. No dispatch capabilities.",
)
store = Store(Path(os.environ.get("ARGUS_DB", ROOT / "data/argus.sqlite")))


@app.middleware("http")
async def local_write_guard(request: Request, call_next: Any) -> Any:
    # WHY: Cross-site pages must not be able to write to a localhost operator console.
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and origin not in {
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:7860",
            "http://localhost:7860",
        }:
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "Cross-origin write rejected"}, status_code=403)
    return await call_next(request)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "version": "1.0.0", "mode": "local-research", "gpu_required": False}


@app.get("/api/incidents", response_model=list[IncidentRecord])
def incidents() -> list[IncidentRecord]:
    return store.list()


@app.get("/api/incidents/{incident_id}", response_model=IncidentRecord)
def incident(incident_id: str) -> IncidentRecord:
    try:
        return store.get(incident_id)
    except KeyError as error:
        raise HTTPException(404, "Incident not found") from error


@app.post("/api/incidents/{incident_id}/decision", response_model=IncidentRecord)
def decide(incident_id: str, body: DecisionRequest) -> IncidentRecord:
    try:
        return store.decide(incident_id, body)
    except KeyError as error:
        raise HTTPException(404, "Incident not found") from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error


@app.get("/api/audit")
def audit() -> list[dict[str, Any]]:
    return store.audit()


@app.get("/api/config")
def config() -> dict[str, Any]:
    return {"actions": [a.value for a in Action], "factors": read_config("severity_factors.yaml")["factors"]}


@app.get("/api/metrics")
def metrics() -> dict[str, Any]:
    path = ROOT / "artifacts/metrics.json"
    return (
        json.loads(path.read_text())
        if path.exists()
        else {"status": "PENDING", "reason": "Run python -m argus.cli eval"}
    )


@app.get("/api/annotations", response_model=list[Annotation])
def annotations(annotator: str) -> list[Annotation]:
    return store.annotations(annotator)


@app.put("/api/annotations", response_model=Annotation)
def annotate(body: Annotation) -> Annotation:
    sources = {source.clip_id: source for source in load_sources()}
    # Research clips registered in incidents are also valid annotation targets.
    sources.update({record.source.clip_id: record.source for record in store.list()})
    if body.clip_id not in sources:
        raise HTTPException(404, "Unknown clip")
    names = set(read_config("severity_factors.yaml")["factors"])
    if set(body.factors) != names or not set(body.accepted_suggestions) <= names:
        raise HTTPException(422, "Exactly the 13 configured factors are required")
    if any(span.end_s > sources[body.clip_id].duration_s for span in body.spans):
        raise HTTPException(422, "Evidence span extends beyond the clip")
    store.save_annotation(body)
    return body


@app.get("/api/adjudication", response_model=list[Annotation])
def adjudication() -> list[Annotation]:
    return [annotation for annotation in store.annotations() if annotation.complete]


@app.get("/api/media/{media_path:path}")
def media(media_path: str) -> FileResponse:
    target = (ROOT / media_path).resolve()
    registered = any((ROOT / r.source.video_path).resolve() == target for r in store.list())
    if target.suffix == ".mp4" and target.with_suffix(".webm").is_file():
        target = target.with_suffix(".webm")
    allowed = [ROOT / "data/sample", ROOT / "data/cache/evidence"]
    if (
        not (registered or any(target.is_relative_to(folder.resolve()) for folder in allowed))
        or not target.is_file()
        or target.suffix.lower() not in {".jpg", ".png", ".mp4", ".webm"}
    ):
        raise HTTPException(404, "Media not found")
    return FileResponse(target)


@app.websocket("/api/runs/{clip_id}")
async def run_socket(socket: WebSocket, clip_id: str) -> None:
    origin = socket.headers.get("origin")
    if origin and origin not in {
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:7860",
        "http://localhost:7860",
    }:
        await socket.close(code=1008)
        return
    await socket.accept()
    source = next((s for s in load_sources() if s.clip_id == clip_id), None)
    if source is None:
        await socket.send_json({"status": "error", "message": "Unknown sample clip"})
        await socket.close()
        return
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def worker() -> None:
        try:
            record = run(
                source,
                ROOT / "data/sample" / f"{clip_id}.claims.json",
                on_event=lambda event: loop.call_soon_threadsafe(queue.put_nowait, event),
            )
            store.put(record)
            loop.call_soon_threadsafe(
                queue.put_nowait, {"status": "finished", "record": record.model_dump(mode="json")}
            )
        except Exception as error:
            loop.call_soon_threadsafe(queue.put_nowait, {"status": "error", "message": str(error)})

    task = asyncio.create_task(asyncio.to_thread(worker))
    try:
        while True:
            event = await queue.get()
            await socket.send_json(event)
            if event["status"] in {"finished", "error"}:
                break
    except WebSocketDisconnect:
        pass
    finally:
        await task


console = ROOT / "apps/console/dist"
if console.exists():
    app.mount("/", StaticFiles(directory=console, html=True), name="console")
