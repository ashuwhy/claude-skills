---
name: web-taste
description: Making web design read as made by a person - the list of AI tells to strip with a replacement for each, the taste profile to aim at, how to name a taste and pin it to evidence, and the numbers that check it. Use before designing or restyling a site, landing page, portfolio or tool UI, when a page looks generic or "AI-made", or when choosing fonts, colours, hover effects and layout.
---

# Web taste

A page reads as AI-made when every choice is the first one a model reaches for. Each tell below is a default that shows up on thousands of pages, so the cost is not that it is ugly, it is that it is recognisable. Strip the tell, then put the one specific thing in its place. These are defaults with reasons; font and palette fashions turn over fast, so the named ones are *(checked 2026-11)*.

Mobile versions of the same tells are in [app-design](../app-design/SKILL.md). Logo and icon work is [brand-identity](../brand-identity/SKILL.md).

## Tells to strip, and what goes there instead

| Tell | Why it reads as generated | Instead |
|---|---|---|
| A small label chip above every heading, plus a one-line subtext under every heading | Same shape on every section is a template; the words say nothing | A label only when it carries data a visitor can use (a date, a stack, a file size). Otherwise the heading stands alone |
| Spotlight cards that follow the cursor, magnetic buttons, a glow that tracks the pointer | The first hover a model writes, on every portfolio | One hover tied to the page's one idea (see below), or a plain colour change |
| Fake HUD: corner readouts, tick rulers, coordinates and altitudes that mean nothing | Numbers with no source look like set dressing | Print a real number or print nothing. Tools show true values: label, value, reset, on every control |
| The default type pairing: Inter, Geist, Space Grotesk or DM Sans with Instrument Serif or Fraunces as the "creative" serif | Everyone's fallback, so it reads as no choice | Pick the face from the subject, test two unusual candidates at real sizes, keep one. A single family used with weight and size contrast beats a safe pair |
| Cream, sand or beige as the new neutral; purple or blue glow; gradient text; neon; pastel blobs | Warm neutrals are now the safe pick and glow is the older one; both are what a model emits unprompted | A ground plus one or two low-chroma inks (below) |
| Three identical cards in a row, cards inside cards, a rounded icon tile over every heading, "01" over a rule, a hairline under every row | Structure by template, not by content | Let content set the shape: one wide item, one tall, uneven columns. Fewer containers; spacing does the grouping |
| A hero-metric block, or a split header with a tiny explainer on the right | Dashboard furniture on a page that is not a dashboard | State the one thing in the hero at full size |
| The same fade-up on every section | Motion that does not answer anything | Content that is already loaded stays still. Move things in response to a pointer or to carry meaning |
| Pure `#000`, or a neutral grey-black, as the dark ground | Reads dead and flat | Tinted near-black, hue pulled toward the ink colour |
| Grey text on a coloured ground, big blurred drop shadows, a coloured stripe down a card's left edge | All three are stock card styling | Text that is a tint of the ground's own hue; flat surfaces; a 1px inner outline instead of a shadow |
| Copy that says it in three lines, em-dashes, round invented metrics, Acme and John Doe | The cadence is the fingerprint | One line. Plain hyphens. Real names and real figures, or leave the slot out |
| Effects scattered over components, each with its own trick | No page-level idea, so no identity | One named motif (below) |

If a page shows five of these, do not patch them one by one. Restart from the profile.

## The taste profile

Aim for this, in plain words, then check each point against a real example you can point at.

- **One idea per page, repeated.** A field of characters, a single curve of light, a grain. One tactile object, not two metaphors. At most one object that breaks the frame.
- **Colour is a ground and one or two inks.** Low chroma, roughly 60% ground, 30% second surface, 10% accent. The accent marks something; it is never decoration. Name a palette as "ground + two inks" so it can be recalled and compared.
- **Dark works when something is lit.** A dark page needs a lit face, a rim, a lit patch of cells in a visible share of the frame. Measured against a good dark reference, the floor was about 25% of cells printed and 10% lit; the share of black pixels is the wrong metric.
- **Texture sits under the threshold of reading.** Noise about 8 luma over the ground, quiet behind text, waking under the cursor. A clear zone round copy. Grain that never stops, stepped at about 24 fps, mono.
- **Small type placed by hand around a subject, used once per page.** Corners, a boxed word on a leader line, a tiny tracked sign-off. Used everywhere it becomes the template again. Handwriting only if it is a scan of the owner's own.
- **Specificity over coverage.** A real screenshot on a flat ground with a 1px inner outline at about 10% of the text colour. Never a gradient behind it, never a stock device frame.
- **Tools show their numbers.** Label, value, track and reset on every control; no account wall; export as format cards.

Motion, kept short: ease-out for enter and exit, interface motion under 300ms, and frequency sets the size (seen fifty times a day, barely moves). Reduced motion gets a gentler version, not none. Never `transition: all`, never `scale(0)`, and gate hover effects behind `@media (hover: hover)`.

## Naming a taste

Liking a thing is not a brief. To make it one:

1. Collect 20 to 40 frames or screenshots the user likes, and group them on boards (light, figures, dark, colour, type, objects, and one board of things they reject).
2. Write the taste as a profile in plain words, a handful of sentences.
3. Pin every claim to a frame. A claim with no frame behind it comes out.
4. Look for what the frames share that has nothing else in common. Here five unrelated inputs turned out to share one curve of light; the user liked the shape, not the film it came from. Name that.
5. Write the rulebook with a source in brackets on each rule.
6. Where two rules fight, write the pick and the reason in a table, so the next decision is already made:

| Rule A | Rule B | Pick | Reason |
|---|---|---|---|
| Quiet behind text | Visible texture | Texture, with a clear zone round copy | Both hold if the zone is real |

7. Settle open choices with the user one question at a time, with a mock for each option, never a paragraph of options. A page of 16 mocked directions across the same 7 surfaces (home, index, detail, wallpaper, link preview, wide screen, phone) made the pick quick because the surfaces stayed fixed and only the direction changed.

Every surface that shows the direction follows it. The link preview shows the same card the page shows, drawn from the same source; change one, change all in one commit, and look at them side by side before calling it done.

## Measure, do not assert

A taste claim that cannot be measured stays a guess. Take the number from the rendered page or frame:

- Printed-cell share and lit-cell share per frame, for character or dither fields.
- Luma standard deviation on the ground, and the luma gap between texture and ground (about 8, floor roughly 3 sd).
- Gap and padding in px between a subject and its small type, between neighbouring components, and at both edges.
- Contrast of text against its ground, after the texture is on.
- Frame cost: GPU ms per frame and fps on a mid laptop and a budget phone, not the dev machine alone.
- Count of the tells above left on the page. The target is zero.

Report measured numbers from a benchmark page and from the live site separately, because they differ.

## Before calling a page done

1. Walk the tell table once, top to bottom, against the rendered page, not the code.
2. Name the page's one idea in a sentence. If it takes two, one of them goes.
3. Check every surface that carries the direction: page, preview card, favicon, wallpaper, phone.
4. Run the measurements and write the numbers down.
5. Read the copy aloud. Cut every line a visitor would skip.
