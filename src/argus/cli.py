from __future__ import annotations

import argparse
import json
import shutil

from argus.config import ROOT, write_json


def demo() -> None:
    from argus.api.store import Store
    from argus.data.sample import generate
    from argus.orchestrator import run

    records = []
    database = Store(ROOT / "data/argus.sqlite")
    existing = {record.source.clip_id: record for record in database.list()}
    public = ROOT / "apps/console/public/demo"
    public.mkdir(parents=True, exist_ok=True)
    for source in generate():
        record = run(source, ROOT / "data/sample" / f"{source.clip_id}.claims.json")
        if source.clip_id not in existing:
            database.put(record)
        records.append(record.model_dump(mode="json"))
        for suffix in (".mp4", ".webm", ".jpg"):
            shutil.copy2(
                ROOT / "data/sample" / f"{source.clip_id}{suffix}", public / f"{source.clip_id}{suffix}"
            )
        assert record.m1_features and record.m3_evidence
        shutil.copy2(
            ROOT / record.m1_features.cache_path, ROOT / "data/sample" / f"{source.clip_id}.features.npy"
        )
        write_json(ROOT / "data/sample" / f"{source.clip_id}.evidence.json", record.m3_evidence.model_dump())
        print(
            json.dumps(
                {
                    "clip": source.clip_id,
                    "ms": record.timing_ms["total"],
                    "state": record.human.state,
                    "rejected": record.m5_verification.n_rejected if record.m5_verification else 0,
                }
            )
        )
    write_json(public / "incidents.json", records)
    write_json(ROOT / "data/sample/incidents.json", records)
    from argus.eval.suite import evaluate

    evaluate()
    print("Sample pipeline complete. Start: python -m argus.cli serve")


def main() -> None:
    parser = argparse.ArgumentParser(prog="argus")
    parser.add_argument("command", choices=["demo", "serve", "eval", "data", "schema"])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.command == "demo":
        demo()
    elif args.command == "serve":
        import uvicorn

        uvicorn.run("argus.api.app:app", host="127.0.0.1", port=args.port)
    elif args.command == "eval":
        from argus.eval.suite import evaluate

        evaluate()
    elif args.command == "data":
        from argus.data.fetch import fetch_all

        fetch_all()
    elif args.command == "schema":
        from argus.api.app import app

        write_json(ROOT / "apps/console/openapi.json", app.openapi())


if __name__ == "__main__":
    main()
