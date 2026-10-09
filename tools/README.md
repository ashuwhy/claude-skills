# Tools

Scripts built during a launch, kept here so the next app starts with them. Check each against the current API before trusting it; they were last run in Oct 2026.

## play.py

Google Play Developer API from the command line: tracks, testers, vitals, errors, release notes, upload, Play-signed APK download, release to the closed track, promote to production with staged rollout, listing icon and store art, and a summary of the Console's installs CSV. Replaces EAS submit and most Console clicking.

Setup, once per app:

1. A Google Cloud service account with the Android Publisher API enabled, invited in Play Console > Users and permissions with release rights.
2. `gcloud auth activate-service-account --key-file=<service-account.json>`. Auth goes through gcloud so the private key never has to be read by the script. Keep the key file out of git.
3. Set `PLAY_PACKAGE`, `PLAY_TRACK` (the closed track's display name) and `PLAY_ACCOUNT` (the service account email), e.g. in the repo's `.envrc`.
4. Copy `play.py` into the repo (`tools/play.py`) so the repo's ship skill has a stable path.

`./play.py --help` lists the commands. The `expo-release` skill describes the release flow built on it.

## mcp-lazy

A stand-in for a stdio MCP server: answers `initialize` and `tools/list` from a cache, starts the real server on the first tool call, stops it after `--idle` seconds (default 600). Saves a resident node process per open session for servers that are rarely called. `--reauth ARG` reruns the server's own login when a call fails with `invalid_grant`.

```
mcp-lazy <name> [--idle SECONDS] [--reauth ARG] -- <command> [args...]
```

In `~/.claude.json`, set the server's `command` to `~/.local/bin/mcp-lazy` and move the original command after `--`. After upgrading a wrapped server, delete `~/.cache/mcp-lazy/<name>.json` so the tool list is re-read. `install.sh` links it into `~/.local/bin`.

## brand/

Two of these run on any app as they are:

```
python make_fonts.py Font-Variable.ttf --sets latin,greek --chars "₹" --pin wdth=100 --out web/src/app/fonts/font.woff2
python make_versus.py candidates.json versus.png [--font Label.ttf]
```

`make_fonts.py` cuts a font to woff2 with Google's latin (or latin-ext, greek, maths) ranges plus any extra characters, axes kept unless pinned. `make_versus.py` takes two or three finalist icons (SVG or PNG, square or Android adaptive layers, plus an optional monochrome layer) and lays out the versus sheet. The format of `candidates.json` is in its docstring. `--help` on either lists the options.

The rest are the scripts behind one app's logo and store art. They draw that app's mark and read its repo layout, so they are reference implementations: read them for the method, copy the parts that fit, and change the drawing, paths and copy. Needs `rsvg-convert`, Pillow, fontTools (plus brotli and uharfbuzz for some) and headless Chrome.

| Script | Method worth reusing |
|---|---|
| `logo-prompts.md` | A shared image-model brief plus one line per concept |
| `make_lockups.py` | Text outlined to SVG paths with HarfBuzz and fontTools; shared helpers the others import |
| `make_round3.py` | Finalist marks redrawn as parameterised SVG |
| `make_icons.py` | Every launcher, adaptive, monochrome, notification, splash, favicon and store icon from one drawing |
| `make_store.py` | Store screenshots and feature graphic as HTML frames rendered by headless Chrome |
| `make_thumbnail.py` | Posters laid out for every crop the app makes |

The `brand-identity` skill describes the process these serve.
