#!/usr/bin/env python3
"""Download English closed captions for each scraped workout.

The HLS master playlist (offers[0].hlsUrl) lists WebVTT subtitle renditions;
the subtitle segments are plain text. Each workout's captions are saved to
data/captions/<id>.txt as "mm:ss<TAB>text" lines. Already-fetched workouts are
skipped, so this is safe to re-run.
"""
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "data" / "api"
OUT = ROOT / "data" / "captions"
UA = "AppleCoreMedia/1.0"
SEGMENT_WORKERS = 6
CUE_TIME = re.compile(r"^(\d\d):(\d\d):(\d\d)\.\d+ -->")


def get(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))


def parse_vtt(text):
    cues, start, lines = [], None, []
    for raw in text.split("\n") + [""]:
        line = raw.strip()
        m = CUE_TIME.match(line)
        if m:
            h, mi, s = map(int, m.groups())
            start, lines = h * 3600 + mi * 60 + s, []
        elif not line:
            if start is not None and lines:
                cues.append((start, " ".join(lines)))
            start, lines = None, []
        elif start is not None:
            lines.append(re.sub(r"\s+", " ", line.replace("\r", " ")).strip())
    return cues


def captions_for(workout):
    hls = workout["attributes"]["offers"][0]["hlsUrl"]
    master = get(hls)
    m = re.search(r'TYPE=SUBTITLES[^\n]*LANGUAGE="en"[^\n]*URI="([^"]+)"', master)
    if not m:
        return None
    sub_url = m.group(1)
    base = sub_url.rsplit("/", 1)[0]
    segs = [l.strip() for l in get(sub_url).splitlines() if l.strip() and not l.startswith("#")]
    urls = [seg if seg.startswith("http") else f"{base}/{seg}" for seg in segs]
    with ThreadPoolExecutor(SEGMENT_WORKERS) as pool:
        bodies = list(pool.map(get, urls))
    seen, out = set(), []
    for body in bodies:
        for t, txt in parse_vtt(body):
            if (t, txt) not in seen:
                seen.add((t, txt))
                out.append(f"{t // 60:02d}:{t % 60:02d}\t{txt}")
    return "\n".join(out)


def work(path):
    wid = path.stem
    dest = OUT / f"{wid}.txt"
    if dest.exists():
        return wid, "cached"
    try:
        text = captions_for(json.loads(path.read_text()))
    except Exception as e:
        return wid, f"error: {e}"
    if text is None:
        return wid, "no english subtitles"
    dest.write_text(text)
    return wid, "ok"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = sorted(API.glob("*.json"))
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    done = 0
    with ThreadPoolExecutor(workers) as pool:
        for wid, status in pool.map(work, paths):
            done += 1
            if status not in ("ok", "cached"):
                print(f"{wid}: {status}")
            if done % 50 == 0:
                print(f"{done}/{len(paths)}", flush=True)
    print(f"{len(list(OUT.glob('*.txt')))} caption files")


if __name__ == "__main__":
    main()
