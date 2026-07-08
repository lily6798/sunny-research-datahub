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

## Adding a new dashboard

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
