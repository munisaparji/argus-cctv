import argparse
import json
from pathlib import Path

from argus.api.store import Store
from argus.config import ROOT, write_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/sirb/release"))
    args = parser.parse_args()
    store = Store(ROOT / "data/argus.sqlite")
    sources = {r.source.clip_id: r.source for r in store.list()}
    rows = [
        a.model_dump(mode="json")
        for a in store.annotations()
        if a.complete and a.clip_id in sources and not sources[a.clip_id].sample
    ]
    if not rows:
        raise SystemExit(
            "No completed real-source annotations. Synthetic practice labels cannot become SIRB research labels."
        )
    args.output.mkdir(parents=True, exist_ok=True)
    for row in rows:
        row["source_dataset"] = sources[row["clip_id"]].dataset
        row["licence"] = "CC-BY-4.0"
    (args.output / "sirb_v1.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    write_json(
        args.output / "release_metadata.json",
        {
            "title": "SIRB annotations",
            "version": "1.0",
            "license": "CC-BY-4.0",
            "records": len(rows),
            "video_included": False,
            "doi": None,
            "publication_status": "LOCAL_UNPUBLISHED",
        },
    )
    print(f"Exported {len(rows)} annotations without video. Confirm source terms before public release.")
