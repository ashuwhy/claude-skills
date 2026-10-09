---
name: brand-identity
description: Logo, app icon and store-art process - brief, image-model rounds, a versus sheet that tests finalists at real sizes, then one drawing in code rendered to every launcher, adaptive, notification, splash, favicon, font and store asset. Use when choosing a logo, producing app icons, or making store screenshots and posters.
---

# Brand identity

The process below is the durable part. Image models, icon specs and store sizes change; check the current platform spec before rendering anything, and *(checked 2026-10)* marks the sizes most likely to move.

Reference scripts live in `~/claude-skills/tools/brand/`: prompts, candidate drawing, the versus sheet, the asset renderer, font subsetting, store frames and posters. They were written for one app and draw its mark, so read them for the method and adapt rather than run them as-is. They need `rsvg-convert`, Pillow, fontTools and headless Chrome.

## 1. Brief

One shared brief pasted ahead of every concept (`tools/brand/logo-prompts.md` is a worked one):

- where it will be used (launcher icon, store listing), so it must read at 48px and survive as a one-colour silhouette
- flat vector, solid shapes, no gradients, shadows, 3D, texture or text
- the exact palette as hex, and "nothing else"
- one centred mark on a rounded-square tile
- several variations in a grid per run, so a run explores a concept instead of betting on one render
- a ban list of the category's clichés

Done when: the brief fits one paragraph and each concept is one extra line.

## 2. Rounds

- **Round 1**: six or seven concepts plus one open brief. Pick one.
- **Round 2**: hold the winner and vary one axis per prompt (geometric versus rounded, what the accent means, the counter, the small single-colour stress test). Spell out letter anatomy in words; models confuse similar glyphs across scripts.
- **Show people outside the build before going further.** How a script, symbol or colour reads to the audience can sink a mark that no prompt would catch. One outside comment is worth a round.
- **Round 3** test: could a child draw it from memory after one look? Credit any sketch to whoever drew it.

## 3. Versus sheet

Redraw the two or three finalists in code (SVG strings), then put them through what a launcher icon actually meets:

- the circle and squircle masks
- a blurred "at a glance" view
- themed (monochrome) icons in light and dark system tones
- 48, 32, 24 and 16px, shown enlarged
- ink share, and a one-line verdict per candidate

Trust the sheet over a preference. A mark that needs explaining loses to one that reads as itself first.

Done when: one candidate wins on the sheet and I can say in a sentence why.

## 4. One drawing, every asset

The winner becomes a function with parameters (colours, detail on or off below a size). One script renders every asset from it; [icon-assets.md](icon-assets.md) has the matrix and the rule behind each size. In the app, draw the mark with a component from the same numbers rather than shipping PNGs, so it is sharp at every size and can flip colour in dark mode.

Then a logo kit (lockups and bare mark, light and dark, SVG and PNG) in the repo's docs, so nobody screenshots the app for a logo.

## 5. Type

Self-host fonts, subset to woff2 with fontTools (the scripts the product needs plus its currency and symbols), variable axes kept. A build that downloads fonts has a network dependency that can fail a deploy. *(checked 2026-10: `next/font/google` failed a Vercel build this way.)*

## 6. Store art and posters

- Render store frames as HTML through headless Chrome to the store's current sizes *(checked 2026-10: Play phone shots 1080x1920, feature graphic 1024x500, listing icon 512px RGB with no alpha)*. Use real captures from a real phone inside a drawn frame. Chrome can exit non-zero after writing, so treat the output file as the success signal.
- No real user's name or data on any screen, and every claim in the copy true of the build under review.
- Upload with `play.py icon` and `play.py art` (see `expo-release`). The listing icon is its own asset; no build changes it.
- Posters and thumbnails: design for every crop the app makes, and upload each render to a new path (see `mobile-performance`, Images).
