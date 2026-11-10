# Fitness+ Yoga Search

Free-text search over every Apple Fitness+ yoga workout: poses, body focus, mood (pre-sleep,
strength…), trainer, length, music. Each result links to `fitness.apple.com/workout/…`, which opens the
workout directly in the Fitness app on iPhone/iPad.

Search examples: `hips hamstrings 20`, `sleep`, `core plank jessica`, `pigeon slow`, `taylor swift`,
`chair standing energetic`. The 🎲 button picks one of the best matches at random.

## How the data is gathered

| Step | Script | Source |
| --- | --- | --- |
| 1. Workout IDs | — | `data/catalog.tsv`: one line per workout (`id`, `modality`, `release date`, `title`, tab-separated). The website has no way to list workouts, so the IDs have to come from a device with Fitness+; this needs access to the iOS filesystem and isn't covered here |
| 2. Metadata | `scripts/scrape.py` | Public catalog API used by fitness.apple.com (`amp-api.fitness.apple.com`, anonymous web token taken from the page): description, trainer, episode, length, skill level, music genre, songs |
| 3. Captions | `scripts/captions.py` | English WebVTT subtitles from each workout's public HLS playlist, so every pose the trainer cues is searchable, not just the 3–5 in the description |
| 4. Build | `scripts/build.py` | Merges the above with the community spreadsheet (`Weekly Workouts.dtable`, matched on link / date+trainer+episode) and tags poses, pose types, body focus and moods using `scripts/vocab.py` |

Outputs:

- `site/index.html` + `site/workouts.json`: the search page (deployed to GitHub Pages)
- `site/yoga.html`: the same page with data inlined, a single file that works offline
- `data/yoga_filled.csv`: the spreadsheet's Yoga table with all gaps filled, for re-import

The ID list, raw captions and API responses stay in `data/` (git-ignored). Only derived tags are published.

## Refreshing (weekly, after new workouts drop on Mondays)

```sh
# refresh data/catalog.tsv with the new IDs first
python3 scripts/scrape.py          # only fetches new IDs
python3 scripts/captions.py        # only fetches new captions
python3 scripts/build.py
git commit -am "Update workouts" && git push   # redeploys Pages
```

Other workout types work too, e.g. `python3 scripts/scrape.py Pilates "Mindful Cooldown"`, but
`build.py` and the vocab are tuned for yoga.

## How tagging works

- **Poses**: alias patterns per pose (`down dog` / `downward-facing dog` / `downdog`…) counted in captions
  and description. Poses named in the description are shown in **bold** and rank higher.
- **Body focus**: body-part mentions per minute compared with the corpus average, so constant alignment cues
  ("feet hip-width apart") don't count. Body parts named in the description always count.
- **Pose types**: same relative approach for Standing, Seated, Backbend, Twists, Hip Opener, Core, etc.,
  plus the spreadsheet's hand tags.
- **Sleep & Wind Down**: explicit sleep/evening wording in the description or the spoken intro, *or* a slow
  flow whose poses are mostly seated/reclined.
- Apple's `skillLevel` maps exactly to Flow Style (High = Energetic, Low = Slow).
