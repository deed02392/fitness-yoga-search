#!/usr/bin/env python3
"""Merge API metadata, captions and the community spreadsheet into site/workouts.json."""
import csv
import json
import re
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import vocab  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
INTRO_SECONDS = 90
GENERIC_BODY = {"Feet", "Arms", "Legs", "Back"}  # cued constantly for alignment, not focus
SLEEP_RE = re.compile(r"\bsleep|bedtime|before bed|\bbed\b|\bevening|end of (?:the|your|a long) day|tonight")


def load_sheet():
    """Spreadsheet rows from the SeaTable export, keyed for matching to API records."""
    z = zipfile.ZipFile(DATA / "Weekly Workouts.dtable")
    table = next(t for t in json.loads(z.read("content.json"))["tables"] if t["name"] == "Yoga")
    key = {c["name"]: c["key"] for c in table["columns"]}
    opts = {c["name"]: {o["id"]: o["name"] for o in (c.get("data") or {}).get("options", [])}
            for c in table["columns"]}

    def val(row, name):
        v = row.get(key[name])
        if isinstance(v, list):  # ids whose option was deleted from the sheet are dropped
            return [opts[name][x] for x in v if x in opts[name]]
        return opts[name].get(v, v) if opts[name] else v

    rows = []
    for r in table["rows"]:
        m = re.search(r"/(\d{9,})", val(r, "Link") or "")
        rows.append({
            "id": m.group(1) if m else None,
            "date": val(r, "Date"), "trainer": val(r, "Trainer"), "ep": val(r, "Ep"),
            "duration": val(r, "Duration"),
            "style": val(r, "Flow Style"), "practice": val(r, "Practice Type"),
            "types": val(r, "Types of Poses") or [], "notable": val(r, "Notable Poses") or [],
            "themes": val(r, "Theme") or [], "notes": val(r, "Notes") or "",
            "prenatal": bool(val(r, "Prenatal")),
        })
    return rows


def catalog_titles():
    """Display titles (which include e.g. "• Music by …") from data/catalog.tsv."""
    rows = [line.split("\t") for line in (DATA / "catalog.tsv").read_text().splitlines() if line]
    return {r[0]: r[3] for r in rows if len(r) > 3}


def load_captions(wid):
    p = DATA / "captions" / f"{wid}.txt"
    if not p.exists():
        return None
    cues = []
    for line in p.read_text().splitlines():
        ts, _, text = line.partition("\t")
        m, s = ts.split(":")
        cues.append((int(m) * 60 + int(s), text))
    return cues


def write_csv(out):
    """The spreadsheet's Yoga table with gaps filled, in its own column names, for re-import."""
    df = Counter(p for w in out for p in w["poses"])
    captioned = sum(w["captioned"] for w in out) or 1
    rows = []
    for w in sorted(out, key=lambda x: (x["date"], x["id"])):
        distinctive = [p for p, n in w["poses"].items() if n >= 2 and df[p] / captioned < 0.15]
        notable = w["notable"] or sorted(set(w["dposes"]) | set(distinctive))
        rows.append({
            "Date": w["date"], "Workout Type": "Yoga", "Duration": f"{w['dur']} min",
            "Trainer": w["trainer"].split()[0], "Ep": w["ep"], "Music": w["music"], "Flow Style": w["style"],
            "Practice Type": w["practice"] or "", "Prenatal": w["prenatal"],
            "Types of Poses": ", ".join(w["types"]), "Notable Poses": ", ".join(notable),
            "Body Focus": ", ".join(w["body"]), "Moods": ", ".join(w["moods"]),
            "Theme": ", ".join(w["themes"]), "Description": w["desc"], "Link": w["url"],
            "Notes": w["notes"], "All Poses (from captions)": ", ".join(f"{p} ({n})" for p, n in w["poses"].items()),
        })
    with open(DATA / "yoga_filled.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)


def main():
    titles = catalog_titles()
    sheet = load_sheet()
    workouts = [json.loads(p.read_text()) for p in sorted((DATA / "api").glob("*.json"))]

    recs = []
    for w in workouts:
        a, rel = w["attributes"], w["relationships"]
        people = [c.get("attributes", {}).get("name", "") for c in rel["contributors"]["data"]]
        desc = a["description"]["standard"]
        cues = load_captions(w["id"])
        spoken = " ".join(t for _, t in cues) if cues else ""
        intro = " ".join(t for s, t in cues if s < INTRO_SECONDS) if cues else ""
        recs.append({
            "w": w, "a": a, "people": people, "desc": desc, "cues": cues,
            "dur": round(a["durationInMilliseconds"] / 60000),
            "desc_poses": vocab.counts(desc, vocab.POSE_RE),
            "cap_poses": vocab.counts(spoken, vocab.POSE_RE),
            "desc_body": vocab.counts(desc, vocab.BODY_RE),
            "cap_body": vocab.counts(spoken, vocab.BODY_RE),
            "moods": vocab.counts(desc, vocab.MOOD_RE), "intro": intro,
        })

    # Corpus baseline: mentions per minute of each body area, to spot unusual emphasis.
    base = {}
    for area in vocab.BODY:
        rates = [r["cap_body"].get(area, 0) / max(r["dur"], 1) for r in recs if r["cues"]]
        base[area] = max(statistics.mean(rates), 0.01)
    type_base = {}
    for c in vocab.TYPE_WORDS:
        rates = [sum(n for p, n in r["cap_poses"].items() if c in vocab.POSES[p][1]) / max(r["dur"], 1)
                 for r in recs if r["cues"]]
        type_base[c] = max(statistics.mean(rates), 0.01)

    # Match spreadsheet rows: by link id, then (date, trainer, ep), then (trainer, ep).
    def first(n):
        return (n or [""])[0].split()[0] if n else ""
    by_id = {r["w"]["id"]: r for r in recs}
    by_key, by_ep = {}, defaultdict(list)
    for r in recs:
        tr = first(r["people"])
        by_key[(r["a"]["releaseDate"], tr, r["a"].get("episodeNumber"))] = r
        by_ep[(tr, r["a"].get("episodeNumber"))].append(r)
    matched = Counter()
    for row in sheet:
        r = by_id.get(row["id"]) or by_key.get((row["date"], row["trainer"], row["ep"]))
        if not r and len(by_ep[(row["trainer"], row["ep"])]) == 1:
            r = by_ep[(row["trainer"], row["ep"])][0]
        if not r:
            cands = [c for c in recs if c["a"]["releaseDate"] == row["date"] and first(c["people"]) == row["trainer"]
                     and row["duration"] and abs(c["dur"] - int(row["duration"].split()[0])) <= 2]
            r = cands[0] if len(cands) == 1 else None
        matched["matched" if r else "unmatched"] += 1
        if r:
            r["sheet"] = row
    print("spreadsheet rows:", dict(matched))

    out = []
    for r in recs:
        w, a, sh = r["w"], r["a"], r.get("sheet", {})
        dur = max(r["dur"], 1)
        poses = Counter(r["cap_poses"])
        for p, n in r["desc_poses"].items():
            poses[p] = max(poses[p], n)

        body = {}
        for area in vocab.BODY:
            ratio = r["cap_body"].get(area, 0) / dur / base[area]
            score = ratio + (3 if area in r["desc_body"] else 0)
            if area in r["desc_body"] or (area not in GENERIC_BODY and ratio >= 1.6
                                          and r["cap_body"].get(area, 0) >= 4):
                body[area] = round(score, 1)

        cat = Counter()
        for p, n in poses.items():
            for c in vocab.POSES[p][1]:
                cat[c] += n
        desc_types = vocab.counts(r["desc"], vocab.TYPE_RE)
        for p in r["desc_poses"]:
            desc_types.update({c: 1 for c in vocab.POSES[p][1]})
        types = sorted(set(sh.get("types", [])) | set(desc_types)
                       | {c for c, n in cat.items() if n >= 3 and n / dur / type_base[c] >= 1.5})

        # Moods come from the description; the spoken intro only counts for explicit time-of-day cues.
        moods = set(r["moods"])
        intro_moods = vocab.counts(r["intro"], {"Sleep & Wind Down": SLEEP_RE, "Morning": vocab.MOOD_RE["Morning"]})
        moods |= set(intro_moods)
        style = sh.get("style") or ("Slow" if a.get("skillLevel") == "Low" else "Energetic")
        if style == "Slow" and re.search(r"relax|restor|calm|gentle|unwind|soothing|longer holds", r["desc"], re.I):
            moods.add("Relax & Restore")
        # Floor-based, slow, few planks/standing: a good pre-sleep candidate even if not labelled as such.
        floor = sum(n for p, n in poses.items() if {"Seated", "Reclined"} & set(vocab.POSES[p][1]))
        upright = sum(n for p, n in poses.items()
                      if {"Standing", "Standing Balance", "Arm Balance"} & set(vocab.POSES[p][1])
                      or p in ("Plank", "Chaturanga", "Side Plank", "Vinyasa", "Downward-Facing Dog"))
        floor_share = floor / max(floor + upright, 1)
        if style == "Slow" and r["cues"] and floor_share >= 0.55:
            moods.add("Sleep & Wind Down")
            moods.add("Relax & Restore")

        songs = [s.get("attributes", {}) for s in w["relationships"].get("songs", {}).get("data", [])]
        genres = [g.get("attributes", {}).get("name") for g in w["relationships"]["genres"]["data"]]
        title = titles.get(w["id"]) or a["name"]
        out.append({
            "id": w["id"],
            "url": a["url"].replace("fitness.apple.com/us/", "fitness.apple.com/"),
            "title": title, "date": a["releaseDate"], "ep": a.get("episodeNumber"),
            "dur": r["dur"], "trainer": r["people"][0] if r["people"] else "",
            "with": r["people"][1:], "music": genres[0] if genres else "", "style": style,
            "desc": r["desc"],
            "poses": dict(poses.most_common()),
            "dposes": sorted(r["desc_poses"]),
            "notable": sh.get("notable", []),
            "types": types,
            "body": dict(sorted(body.items(), key=lambda kv: -kv[1])),
            "moods": sorted(moods),
            "themes": sh.get("themes", []), "notes": sh.get("notes", ""),
            "practice": sh.get("practice"), "prenatal": sh.get("prenatal", False),
            "artists": sorted({s.get("artistName", "") for s in songs} - {""}),
            "songs": [f'{s.get("name", "")} – {s.get("artistName", "")}' for s in songs],
            "img": next((x["url"] for x in a.get("artworks", []) if "{w}" in x.get("url", "")), None),
            "captioned": bool(r["cues"]),
        })

    out.sort(key=lambda x: (x["date"], x["id"]), reverse=True)
    write_csv(out)
    SITE.mkdir(exist_ok=True)
    meta = {"built": max(x["date"] for x in out), "count": len(out),
            "poses": {p: {"aliases": v[0], "types": v[1]} for p, v in vocab.POSES.items()},
            "body": list(vocab.BODY), "moods": list(vocab.MOODS)}
    payload = json.dumps({"meta": meta, "workouts": out}, ensure_ascii=False, separators=(",", ":"))
    (SITE / "workouts.json").write_text(payload)
    # Self-contained single file (data inlined), handy for offline use or hosts without static JSON.
    html = (SITE / "index.html").read_text()
    inline = "<script>window.WORKOUTS=" + payload.replace("</", "<\\/") + ";</script>\n<script>"
    (SITE / "yoga.html").write_text(html.replace("<script>", inline, 1))
    print(f"wrote {len(out)} workouts, {sum(x['captioned'] for x in out)} with captions, "
          f"{(SITE / 'workouts.json').stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
