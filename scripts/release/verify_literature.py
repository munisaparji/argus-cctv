from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ARGUS-academic-metadata-check/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)["message"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("docs/literature/verified.json"))
    args = parser.parse_args()
    rows = {}
    for doi in [
        "10.1109/TCSVT.2024.3462433",
        "10.1109/TIP.2024.3451935",
        "10.1109/TMM.2024.3379893",
        "10.1109/TMM.2023.3240881",
    ]:
        data = get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe=""))
        rows[data["DOI"]] = data
    for query in [
        "weakly supervised video anomaly detection",
        "video anomaly detection language evidence",
        "video anomaly detection dynamic erasing",
        "video anomaly detection attention",
    ]:
        params = urllib.parse.urlencode(
            {
                "query.title": query,
                "filter": "type:journal-article,from-pub-date:2023-01-01,until-pub-date:2026-09-11",
                "rows": 30,
            }
        )
        for data in get("https://api.crossref.org/works?" + params)["items"]:
            title = data.get("title", [""])[0]
            if data["DOI"].startswith("10.1109/") and re.search("video.*anomaly|anomaly.*video", title, re.I):
                rows.setdefault(data["DOI"], data)
    selected = list(rows.values())[:15]
    output = []
    for data in selected:
        # WHY: Re-resolve every selected DOI, including search results, before marking metadata verified.
        data = get("https://api.crossref.org/works/" + urllib.parse.quote(data["DOI"], safe=""))
        output.append(
            {
                "title": data["title"][0],
                "doi": data["DOI"],
                "journal": data.get("container-title", [""])[0],
                "year": data.get("published", data.get("issued"))["date-parts"][0][0],
                "authors": [
                    (" ".join([a.get("given", ""), a.get("family", "")])).strip()
                    for a in data.get("author", [])
                ],
                "type": data["type"],
                "abstract": re.sub("<[^>]+>", "", data.get("abstract", "")),
                "verification": "Crossref DOI metadata resolved",
                "url": "https://doi.org/" + data["DOI"],
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps([{"title": r["title"], "doi": r["doi"], "year": r["year"]} for r in output], indent=2))


if __name__ == "__main__":
    main()
