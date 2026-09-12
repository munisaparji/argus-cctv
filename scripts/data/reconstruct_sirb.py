import argparse
import json
from pathlib import Path

import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/sirb/reconstructed.json"))
    args = parser.parse_args()
    index = {r["clip_id"]: r for r in pd.read_parquet(args.index).to_dict("records")}
    output = []
    for line in args.annotations.read_text().splitlines():
        row = json.loads(line)
        if row["clip_id"] not in index:
            raise ValueError(f"Source clip unavailable: {row['clip_id']}")
        output.append({"annotation": row, "source": index[row["clip_id"]]})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Mapped {len(output)} annotations to locally licensed source clips")
