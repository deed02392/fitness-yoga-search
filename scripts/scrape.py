#!/usr/bin/env python3
"""Fetch full workout metadata from the public Fitness+ catalog API.

Workout IDs come from data/catalog.tsv (see README); details come from
amp-api.fitness.apple.com using the anonymous web token that
fitness.apple.com embeds in its pages. Results are cached in data/api/ so
re-runs only fetch new workouts.

usage: scrape.py [modality-name ...]   (default: Yoga)
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = DATA / "api"
API = "https://amp-api.fitness.apple.com/v1/catalog/us/workouts"
INCLUDE = "equipments,body-focuses,contributors,modalities,genres,themes,songs"
BATCH = 50
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15"


def get_token():
    req = urllib.request.Request("https://fitness.apple.com/us/workout/yoga-with-jessica/1849010816",
                                 headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    m = re.search(r'<meta name="web-experience-app/config/environment" content="([^"]+)"', html)
    env = urllib.parse.unquote(m.group(1))
    return re.search(r'"token":"([^"]+)"', env).group(1)


def catalog_ids(modalities):
    """IDs from data/catalog.tsv: id, modality, release date, title (tab-separated)."""
    rows = [line.split("\t") for line in (DATA / "catalog.tsv").read_text().splitlines() if line]
    return [r[0] for r in sorted(rows, key=lambda r: r[2]) if r[1] in modalities]


def fetch(ids, token):
    qs = urllib.parse.urlencode({"ids": ",".join(ids), "include": INCLUDE, "l": "en-US"})
    req = urllib.request.Request(f"{API}?{qs}", headers={
        "Authorization": f"Bearer {token}", "Origin": "https://fitness.apple.com", "User-Agent": UA})
    for attempt in range(5):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503) or attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))


def main():
    modalities = sys.argv[1:] or ["Yoga"]
    CACHE.mkdir(parents=True, exist_ok=True)
    ids = catalog_ids(modalities)
    todo = [i for i in ids if not (CACHE / f"{i}.json").exists()]
    print(f"{len(ids)} workouts in catalog, {len(todo)} to fetch")
    if not todo:
        return
    token = get_token()
    for n in range(0, len(todo), BATCH):
        chunk = todo[n:n + BATCH]
        resp = fetch(chunk, token)
        included = {(x["type"], x["id"]): x for x in resp.get("included", [])}
        for w in resp.get("data", []):
            # Inline related resources so each cached file is self-contained.
            for rel in w.get("relationships", {}).values():
                rel["data"] = [included.get((d["type"], d["id"]), d) for d in rel.get("data", [])]
            (CACHE / f"{w['id']}.json").write_text(json.dumps(w))
        missing = set(chunk) - {w["id"] for w in resp.get("data", [])}
        print(f"  {n + len(chunk)}/{len(todo)}" + (f"  (not in US catalog: {len(missing)})" if missing else ""))
        time.sleep(1)


if __name__ == "__main__":
    main()
