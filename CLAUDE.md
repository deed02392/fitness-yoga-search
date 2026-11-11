# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, phone-friendly search page over every Apple Fitness+ yoga workout (poses, body focus, mood,
trainer, length, music). Results link to `https://fitness.apple.com/workout/<slug>/<id>`, which deep-links
into the Fitness app. Deployed to GitHub Pages from `site/` (public repo: `deed02392/fitness-yoga-search`,
served at `george.hafiz.uk/fitness-yoga-search/`).

## Pipeline / commands

No dependencies beyond Python 3 stdlib. No tests or linter. Run the steps in order; each is incremental:

```sh
python3 scripts/scrape.py [Modality ...]   # default Yoga; fetches only IDs missing from data/api/
python3 scripts/captions.py [workers]      # fetches only workouts missing from data/captions/
python3 scripts/build.py                   # always rebuilds site/ and data/yoga_filled.csv
```

`data/catalog.tsv` (tab-separated `id, modality, release date, title`) is the input to everything and
must be refreshed first when new workouts are released (Mondays). How it's produced is deliberately not
documented in this repo (see the "Public repo" note below).

Pushing to `main` redeploys Pages via `.github/workflows/pages.yml`, but only when `site/**` changes.

## Architecture

- **`scripts/scrape.py`**: batch-fetches (50 IDs/request) from `amp-api.fitness.apple.com/v1/catalog/us/workouts`
  using the anonymous bearer token scraped from the `web-experience-app/config/environment` meta tag on any
  fitness.apple.com workout page. Related resources (`included`) are inlined into each `data/api/<id>.json`.
  The API can't list workouts by modality, which is why IDs come from `catalog.tsv`.
- **`scripts/captions.py`**: `offers[0].hlsUrl` → HLS master playlist → English `SUBTITLES` rendition → WebVTT
  segments (public, unencrypted). Cue line breaks are `\r`. Saves `data/captions/<id>.txt` as `mm:ss\ttext`,
  only after a workout fully succeeds (safe to kill/restart). Requests have ~0.7s latency, so segments are
  fetched in parallel within a workout as well as across workouts.
- **`scripts/vocab.py`**: all tagging vocabularies. `POSES` maps canonical pose → (regex aliases, pose-type
  categories); `BODY`, `MOODS`, `TYPE_WORDS` likewise. Regexes run on `norm()`ed text (lowercase, apostrophes
  stripped, hyphens/slashes → spaces), so write patterns against that form (e.g. `childs pose`, `cat cow`).
  Ambiguous single words (bow, star, hero…) need context-restricted patterns; check matches against
  real captions before adding one.
- **`scripts/build.py`**: merges API data, captions, catalog titles and the community SeaTable export
  (`data/Weekly Workouts.dtable`, a zip; Yoga table in `content.json`). Key design points:
  - Body focus and pose types are **relative to corpus baselines** (mentions per minute vs. the corpus mean),
    because alignment cues (feet, arms, down dog, plank) appear in nearly every flow. Anything named in the
    description always counts.
  - Moods come from the description; the spoken intro (first 90s) only contributes explicit sleep/morning cues.
    "Sleep & Wind Down" is also inferred for slow flows whose poses are ≥55% seated/reclined.
  - Spreadsheet rows match by link ID → (date, trainer first name, ep) → unique (trainer, ep) → (date, trainer,
    duration ±2). Its hand-curated `Notable Poses`/`Types of Poses`/`Theme`/`Notes` are merged in; select-option
    IDs with no surviving option name are dropped.
  - Apple `skillLevel` High/Low ≡ Flow Style Energetic/Slow.
  - Workout URLs have the `/us/` storefront segment removed (the user-tested deep-link format).
- **`site/index.html`**: the whole front end (vanilla JS, no build step). Loads `workouts.json`, or
  `window.WORKOUTS` if inlined. The query is parsed greedily (longest phrase first) into facet terms (pose / body /
  mood / type / trainer / style / music / duration) using the canonical names from `workouts.json` `meta`
  plus the `EXTRA` alias table in the page; leftover words are free-text matched against a haystack. All terms
  are ANDed. Pose scores are linear in the caption count (plus a bonus for description/notable mentions), and each
  term is normalised by its best score across the matches before terms are summed.
  - `-x` / `no x` / `without x` excludes on *any* mention (tag, caption count or haystack word). `GROUPS` are
    pose sets matched on tagged poses only, never on their alias words (e.g. `-wide` → Wide Stance, since captions
    say "shoulder width"). Artists (from `artists`, split on `, ` / ` & `) are facets too.
  - Finished, recognised terms become chips in the search box; a phrase that more typing could change waits for the
    next word, Enter, blur or a 1s pause. Length/trainer/style/music chips are stored in their `<select>`s
    (newest wins); the others live in `CHIPS`. The status line lists every active constraint. State is kept in
    the URL hash (`q` = chips + text, plus select params).
- **`site/yoga.html`** is generated by `build.py` (index.html with the data inlined). Edit `index.html`, not this.

## Working in this environment

- The sandbox can't bind local ports, and the corporate proxy blocks mzstatic images and the Pages domain
  (don't try to bypass the proxy). To check UI changes, run `build.py` and open
  `file://…/site/yoga.html#q=…` in the Chrome DevTools MCP with a mobile viewport. Hash-only navigation
  doesn't reload, so force a reload.
- `data/` is git-ignored except `data/catalog.tsv`, `data/api/` and `data/captions/` (kept as a
  permanent record in case scraping stops working). These, `private/` and `CLAUDE.local.md` are
  committed **age-encrypted** via `.gitattributes` (`filter=age`; the filter and its Keychain-held identity come
  from the user's MacGeorgeface dotfiles, `~/bin/git-age-filter`). They are plaintext in the working tree. Never
  commit them on a machine without the filter (`git config filter.age.clean` must be set), and never add
  plaintext copies elsewhere. File *names* are public, so don't add encrypted files whose names reveal anything.

## Public repo

Nothing committed may reveal how `catalog.tsv` is obtained beyond "needs access to the iOS filesystem".
Before committing, check the staged (i.e. published) blobs for internal app/DB names, device paths and hostnames,
and that every `filter=age` file is actually encrypted (see `CLAUDE.local.md` for the exact commands).
