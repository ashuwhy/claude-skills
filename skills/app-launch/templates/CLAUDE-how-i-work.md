<!-- Template for the "How I work in this repo" section of a new app's CLAUDE.md.
Replace every <ANGLE> placeholder, delete lines that do not apply, delete this
comment. Keep only what the config cannot tell an agent. -->

## How I work in this repo

Things the config does not tell you:

- **Releasing the app**: use the `ship-mobile` skill. A store build goes to the closed track "<TRACK>" first; I update my <PHONE> from the store and test it, then `play.py promote` sends the same build to production. JS-only fixes go out as OTA updates; anything native gets a version bump and a store build.
- **Commits**: one concern per commit, `type(scope): subject` phrased as the outcome a user sees, body says why. I am the only author. Commit and push when I ask.
- **Comments** record a reason, a measurement, or a platform quirk. Match the density of the files around them.
- **Motion** follows `<motion module>`: movement answers a touch, never an arrival, and nothing overshoots. Expensive visuals are gated on `<device tier module>`.
- **Content** changes are database work, not app releases. An empty item is `is_active = false`. Migrations go in `<migrations dir>`.
- **Analytics** is one project for web and app. Event names live in `<mobile events file>` and `<web events file>` and must match; send through `capture()`. Logs go through `<logger>`, never bare `console.*`, with a fixed message and variable data in attributes. Multi-step user actions get a span from `<tracing module>`.
- **No personal data leaves the device** in events, logs or traces. Not a name, email, phone or account identifier. Redaction in `beforeSend` is a backstop, not permission.
- **Testing devices**: <devices>.
- **Payments**: <state of payments>.
- No em dashes in anything written for me; plain hyphens.
