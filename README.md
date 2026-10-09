# claude-skills

My Claude Code skills and tools for building and launching apps, from what I learned taking one app from an empty repo to Google Play production in 2026.

## The rule for everything in here

**Defaults, not law.** Each rule carries the reason it exists. Tools and store policies change, so before a rule is applied its reason gets checked against the current version, and when something better exists the better thing wins and the skill gets fixed. Facts likely to age are marked *(checked YYYY-MM)*. Templates are reference code from the date they were written, checked against current docs before copying.

The skills are there to save time on the next app. A skill that forces an old way has stopped doing its job, and gets fixed the day that is noticed.

## Skills

| Skill | Use it for |
|---|---|
| `app-launch` | Starting a new app: day-one defaults, the order of work, which skill covers what |
| `expo-release` | OTA versus store build, runtime versions, testing a Play-signed build, promotion |
| `play-production-access` | The closed test, testers, evidence and the production application |
| `mobile-performance` | Budget-phone performance: tiers, cold start, lists, images, R8, Android rendering |
| `app-design` | Motion, haptics, spacing, dark mode, tab bar, splash, components, copy |
| `brand-identity` | Logo rounds, versus sheet, every icon from one drawing, fonts, store art |
| `product-analytics` | Events, logs, traces and crashes in one PostHog project, no personal data |
| `supabase-backend` | Policies, entitlement functions, cron upkeep, auth, Google sign-in |
| `nextjs-web` | Auth gate, static rendering, redirects, sign-out, timeouts, latency |

Each skill's `templates/` holds files to copy into a new app.

## Also here

- `tools/`: `play.py` (Play Developer API CLI), `mcp-lazy` (lazy MCP server wrapper), `brand/` (logo and store-art scripts). See [tools/README.md](tools/README.md).
- `lessons/`: dated incident logs, one line per incident with the rule it produced. History for when a rule needs re-judging; no skill loads them.

## Install

```bash
./install.sh
```

Symlinks every skill into `~/.claude/skills` and `mcp-lazy` into `~/.local/bin`. It skips anything already there that is not its own link, and says so. Edits in this repo are live at once through the links.

## Keeping it honest

- A rule proves wrong or outdated: change it, update its reason, re-date it, commit.
- A new lesson: the durable rule goes in the skill with its reason; the dated story and numbers go in `lessons/`.
- Nothing app-specific in a skill: no app names, user counts or one-off figures. Those belong in that app's repo.
- Never commit secrets: service-account keys, `.env` files, tokens.
