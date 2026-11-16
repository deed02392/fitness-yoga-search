#!/usr/bin/env python3
"""Fetch full workout metadata from the public Fitness+ catalog API.

Workout IDs come from data/catalog.tsv: one workout per line, either its
share link from the Fitness app (fitness.apple.com/workout/<slug>/<id>) or
just the ID, optionally followed by a tab and the workout type (Yoga, HIIT…)
so other types are skipped without fetching. Details come from
amp-api.fitness.apple.com using the anonymous web token that
fitness.apple.com embeds in its pages. Only workouts of the requested types
are saved, to data/api/, so re-runs only fetch new ones.

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
    """Workout IDs from data/catalog.tsv (the first long number on each line), in file order."""
    ids = []
    for line in (DATA / "catalog.tsv").read_text().splitlines():
        cols = line.split("\t")
        m = re.search(r"\b(\d{9,})\b", cols[0])
        if m and m.group(1) not in ids and (len(cols) < 2 or cols[1] in modalities):
            ids.append(m.group(1))
    return ids


def modality(w):
    return next((m.get("attributes", {}).get("name") for m in w["relationships"].get("modalities", {}).get("data", [])), None)


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
    print(f"{len(ids)} workouts listed, {len(todo)} not fetched yet")
    if not todo:
        return
    token = get_token()
    for n in range(0, len(todo), BATCH):
        chunk = todo[n:n + BATCH]
        resp = fetch(chunk, token)
        included = {(x["type"], x["id"]): x for x in resp.get("included", [])}
        other = 0
        for w in resp.get("data", []):
            # Inline related resources so each cached file is self-contained.
            for rel in w.get("relationships", {}).values():
                rel["data"] = [included.get((d["type"], d["id"]), d) for d in rel.get("data", [])]
            if modality(w) not in modalities:  # e.g. a non-yoga link in the list
                other += 1
                continue
            (CACHE / f"{w['id']}.json").write_text(json.dumps(w))
        missing = set(chunk) - {w["id"] for w in resp.get("data", [])}
        print(f"  {n + len(chunk)}/{len(todo)}" + (f"  (not in US catalog: {len(missing)})" if missing else "")
              + (f"  (other workout types skipped: {other})" if other else ""))
        time.sleep(1)


if __name__ == "__main__":
    main()
