---
name: web-taste
description: Web design that reads as made by a person - the taste profile to aim at, the AI tells to find and what replaces each, the numbers that check a page, and how to turn references into a named direction. Use when designing or restyling a site, landing page, portfolio or tool UI, when a page looks generic or AI-made, or when picking fonts, palette, hover or layout.
---

# Web taste

A page reads as generated when every choice is the first one a model reaches for. The fix is never one trick. It is one specific idea, carried through every surface, with the defaults stripped out around it. These are my defaults with their reasons; font and palette fashions turn over fast, so the named ones are *(checked 2026-11)*.

Choosing a look from references (boards, mock directions, a pick with the user) is its own job: [naming-a-taste.md](naming-a-taste.md). Logos, favicons and fonts: [brand-identity](../brand-identity/SKILL.md). Mobile screens: [app-design](../app-design/SKILL.md).

## The profile

- **One idea per page, repeated.** Name it in a sentence: a texture, a shape, an object. It is the background or the hero, never an effect attached to components. Nothing else moves as decoration.
- **One object you can hold.** A card, a stamp, a cartridge, a sticker. Lean on it everywhere (gate, link preview, favicon) and add no second metaphor. One object may break the frame; that beats a centred card.
- **Colour is a ground plus one or two inks.** Low chroma. About 60% ground and big surfaces, 30% structure (secondary text, rules, texture at rest), 10% accent for links, the one filled button per view, selection and state. The accent marks; it never decorates. Name each palette "ground + two inks" with a role per hex.
- **The ground is a tinted near-black or a tinted light**, pulled toward the ink's hue, with one neutral family (warm or cool, not both). Text on a coloured ground is a darker or lighter shade of that hue.
- **Two type families.** One sans for everything read, one mono for buttons and labels in caps. The wordmark is set in the sans or drawn as a mark, never a third face. About five sizes on one ratio, body lines near 65 characters, `text-wrap: balance` on headings.
- **Placed type, once per page.** Words set round a subject, a boxed word on a hairline leader, a tiny tracked sign-off. Used once it is a composition; used on every section it is a template again.
- **Labels carry data.** A date, a stack, a size, a live value. A label with nothing to say is cut.
- **Texture sits under the threshold of reading** and quiets round copy. If it reacts to the cursor, that is the page's one interaction, and nothing else draws a trail.
- **Real work, shown readable.** Real screenshots on a flat ground with a faint 1px outline in the text colour, so a light screenshot does not bleed into a dark page.
- **Tools print their numbers.** Every control shows its label, current value, track and reset. No account to get the output; export as a choice of formats.
- **Copy says it once.** One line, real names, real figures, plain hyphens. Specific button labels; an error says how to fix it.

## Tells to find

Walk the rendered page for these.

| Tell | Instead |
|---|---|
| A chip of small caps over every heading, a grey line of subtext under it | The heading alone; a label only where it carries data |
| A hover that follows the cursor: spotlight cards, buttons pulled toward the pointer, a glow | A plain state change, or the page's one interaction |
| Readouts dressed as instruments: corner coordinates, signal strength, tick rulers, numbers with no source | A real value, or empty space |
| The fonts every agent picks (Inter, Geist, Space Grotesk, DM Sans) with Instrument Serif or Fraunces as the flourish | A sans chosen for the subject, compared on the real name and copy |
| Warm paper grounds by default; violet or blue glow; gradient headline text; neon | Ground plus inks, tinted |
| Same-size cards three across, a card nested in a card, an icon in a rounded square over each heading, "01" above a rule | Shape from content: uneven widths, a list, spacing doing the grouping |
| A big number with a tiny caption as the hero; headline left with a small paragraph pinned right | The one thing, said at full size |
| Every section fading up the same way | Stage the hero; the rest arrives quietly or not at all |
| `#000` or a neutral grey-black ground | Near-black tinted toward the ink |
| Soft blurred shadows on everything, a coloured bar down one edge of a card | Flat surfaces, lighter surfaces for depth in dark mode |
| Glitch, scrambled text, VHS lines, matrix rain, pastel blobs, wide techno display faces | The page's own texture, or none |
| Three sentences doing one sentence's work, invented round numbers, placeholder company names | One line, true figures |

Five or more on one page means the problem is upstream: there is no idea yet. Go to [naming-a-taste.md](naming-a-taste.md) instead of patching rows.

## Where rules fight

| Fight | Pick | Why |
|---|---|---|
| A living texture on every page vs. no decorative motion | The texture, if it is the page's one idea | It is the background, not something stuck on components |
| Content still on load vs. a small entrance | One entrance: rise 8-12px and fade, staggered 30-80ms, hero only staged | The web has scroll; a mobile screen does not (app-design keeps entrances out) |
| A narrow reading column vs. empty sides on ultrawide | Keep copy at 560-680px; give the width to the image, field and object | Text stays readable; the things that scale take the space |
| Grain everywhere vs. grain lowering small-type contrast | Grain behind the HTML, never on top of text | Both hold |
| A cursor effect vs. no cursor gimmicks | One, owned by the site, on fine pointers only | One is identity; several is a demo reel |

## Motion

Ease-out for entering and leaving, ease-in-out for moving on screen, never ease-in on interface. Press 100-160ms, tooltip about 160, dropdown about 200, drawers up to 500. Seen fifty times a day, it barely moves; seen once a session, it can take its time. Start from `scale(0.95)` and opacity 0, never `scale(0)`. Name properties instead of `transition: all`. Hover sits behind `(hover: hover) and (pointer: fine)`. Every animation is interruptible. Reduced motion gets fades without travel, a still texture, and no loops. Anything that moves by itself for over 5s beside content gets a pause control.

## Measure it

A taste claim is a guess until it has a number from the rendered page:

- **Contrast** after texture is on: 4.5:1 body, 3:1 large text and buttons. Print the ratios beside the palette.
- **Printed and lit share** for dark or character-drawn frames. Cut the frame into width/160 square cells; a cell is printed when its brightest pixel clears the ground by about 14 luma, lit past about 90. Black-pixel share is the wrong metric. A picture with no copy (an intro, a hero image) wants roughly 25% printed and 10% lit, which is where the dark reference I liked sat. A page of words can sit near 5%, because the copy is what is lit.
- **Texture strength**: marks about 8 luma over the ground read as felt, not seen. Grain is separate: a floor near 3 sd on the ground, rising toward 8 on lit areas. Check at real strength and at 5x boosted, so the pattern can be judged at all.
- **Frame cost**: GPU and JS ms per frame at 1080, 4K and ultrawide, p50 and p95, against the 16.7ms budget.
- **Tell count** from the table above. Zero.

These thresholds came from one dark site's research; treat them as starting points and re-derive them against the references for a new look. Report benchmark and live-site numbers separately.

## Done when

1. The page's one idea fits in one sentence.
2. The tell table, walked against the rendered page at desktop, ultrawide and phone, finds nothing.
3. Every surface that shows the look (page, link preview, favicon, manifest, social card) draws it from the same source, checked side by side.
4. The numbers above are written down with the screen and date they were taken on.
5. The copy, read aloud, has no line a visitor would skip.
