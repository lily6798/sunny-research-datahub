# Sunny Research Assets

Password-protected library of Sunny Advertising research dashboards.
The published site lives in `docs/` — every page is AES-256 encrypted with
[StatiCrypt](https://github.com/robinmoisson/staticrypt), so the content is
unreadable without the team password (ask Lily). Tick **Remember me** when you
unlock and you won't be asked again for 30 days.

## How it fits together (local working copy)

Only the encrypted `docs/` folder is committed — everything else is
git-ignored and stays on Lily's machine:

- `index.html` — the hub page (light Sunny theme, card grid, search + vertical filters)
- `dashboards/` — the plaintext interactive dashboards
- `data/nielsen/` — source Nielsen exports the dashboards are built from
- `build.sh` — encrypts `index.html` + `dashboards/*.html` into `docs/`
- `generator/` — Python pipeline that turns a raw Nielsen Ad Intel `.xlsx` export into a
  full dashboard HTML (see below). This folder *is* committed — it's code, not spend data.

## Generating a dashboard straight from a Nielsen export

For a vertical you have a raw Nielsen Ad Intel `.xlsx` export for (Advertiser × Media Type ×
monthly spend, 12-month rolling), you don't have to hand-build the HTML:

1. Drop the `.xlsx` into `data/nielsen/`.
2. In `generator/verticals.py`, add a new vertical config: a `structure_fn`/`category_fn`
   pair (heuristic, by advertiser name) for the market-structure and segment lenses, plus
   `insights_fn` and `struct_note_fn` for the write-up. Copy an existing vertical
   (e.g. `SPORT_TEAMS`) as a template — most of the work is deciding the 3–4 way
   "market structure" split and the finer ~6–9 way "segment" split for that category.
3. Run it:
   ```bash
   cd generator && source <your venv>/bin/activate  # needs pandas + openpyxl
   python3 verticals.py
   ```
   This writes the finished dashboard straight into `dashboards/`, including a full,
   searchable, segment-filterable list of *every* advertiser (not just the top 25).
4. Add the card to `index.html`'s `ASSETS` array (see below), then `./build.sh` and push.

**Important:** every KPI/insight number must be a named lookup (`structure['Some Bucket']`),
never "whichever bucket is biggest" — a dashboard's #5 KPI label and value went out of sync
early on for exactly that reason (Motor Vehicles' "Chinese challenger" KPI briefly showed the
*Legacy OEM* number, because that bucket happened to be largest). Each vertical config sets
`struct_kpi_key` explicitly to avoid this.

## Adding a hand-built dashboard (no raw data)

1. Drop the dashboard HTML into `dashboards/` (lowercase filename, e.g. `auto-media-spend-2026.html`).
2. Add an entry to the `ASSETS` list at the top of the `<script>` in `index.html`:

```js
{
  title: "Auto — Australian Media Spend",
  vertical: "Auto",                       // drives the filter pills
  desc: "One-to-two line summary of what's inside.",
  period: "Jan – Dec 2026",
  source: "Nielsen Ad Intel",
  file: "auto-media-spend-2026.html",     // filename in dashboards/
  added: "2026-07-09"                     // newest shows first
}
```

3. Rebuild and publish:

```bash
./build.sh
git add docs && git commit -m "Add Auto dashboard" && git push
```

## Changing the password

```bash
./build.sh "NewPassword"
git add docs && git commit -m "Rotate password" && git push
```

Everyone will need the new password (and to re-tick Remember me).

## Hosting

GitHub Pages, served from the `docs/` folder on `main`
(repo Settings → Pages → Deploy from a branch → `main` / `docs`).
