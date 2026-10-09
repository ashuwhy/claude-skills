---
name: app-launch
description: Starting a new app and taking it to the store - day-one defaults, the order of work from empty repo to production, and which skill covers each stage. Use when starting a new app, planning a launch, or unsure which of my app skills applies.
---

# Launching a new app

The skills in `~/claude-skills` hold what one full launch taught me: an Expo app on Google Play with Supabase, PostHog and a Next.js site. They exist to save time, never to pin me to old tools.

**Defaults, not law.** Every rule carries its reason. Before applying one, check the reason still holds for the current version of the tool. If something better exists now (a new SDK feature, a different service, a changed store policy), use it, then fix the skill in `~/claude-skills` and commit, so the next app starts from the better default. Facts marked *(checked YYYY-MM)* are the likeliest to have aged; verify those first.

## Pick the stack fresh

The skills assume Expo, EAS, Supabase, PostHog and Vercel, which were the right picks in 2026. For a new app, spend ten minutes checking each is still the right one before defaulting to it. The principles (OTA versus native lanes, server-decided entitlements, one analytics project, gates proven under dev and build) carry over to whatever replaces them.

## Order of work

| Stage | What gets done | Skill |
|---|---|---|
| Day one | Repo, `CLAUDE.md` "How I work" section from [templates/CLAUDE-how-i-work.md](templates/CLAUDE-how-i-work.md), analytics, release config | this list, then the ones named |
| Identity | Brief, rounds, versus sheet, every icon from one drawing | `brand-identity` |
| Building | Motion, haptics, spacing, dark mode, performance tiers | `app-design`, `mobile-performance` |
| Backend | Policies, entitlement functions, auth, cron upkeep | `supabase-backend` |
| Website and admin | Gate, rendering, redirects, latency | `nextjs-web` |
| First store build and closed test | Release tooling, testers, the evidence | `expo-release`, `play-production-access` |
| Production and after | Promote, stage rollouts, watch p90 and crashes | `expo-release`, `product-analytics` |

## Day one

Each of these is cheap on day one and expensive later, which is why they go first.

- [ ] **Analytics, logs, traces and crash capture in the very first build** (`product-analytics`). Store vitals stay empty for a small audience, and the closed test needs device-level evidence from its first day.
- [ ] **No personal data in any telemetry**, written into the repo's `CLAUDE.md`. Person records never expire, so a mistake on day one lives forever.
- [ ] **Release channels and runtime versioning decided** (`expo-release`). Sharing one channel between testers and production means there is no tester-only OTA.
- [ ] **Code shrinking on from the first store build**, with keep rules, so a missing rule shows up in testing rather than in production.
- [ ] **Device tier and shared motion, haptics and toast modules** (`mobile-performance`, `app-design`), so every screen is built against them instead of retrofitted.
- [ ] **Writes that grant access go through server functions** (`supabase-backend`), never a client RLS insert policy.
- [ ] **Upkeep for anything scheduled**: a purge job beside the first cron job.
- [ ] **Store developer account created and testers recruited early** (`play-production-access`). The closed-test clock is the longest wait in the whole launch.
- [ ] **Release tooling**: `~/claude-skills/tools/play.py` copied into the repo and a per-repo ship skill from `expo-release/templates/ship-SKILL.md`.

Done when: a dev build sends a test event, log, span and exception that show up in an SQL query, and the repo's `CLAUDE.md` says how I work in it.

## Keeping the skills honest

When a skill's advice turns out wrong or outdated during the new app, fix it the same day in `~/claude-skills`: change the rule, update its reason, re-date anything version-bound, commit. A dated incident worth remembering goes in `~/claude-skills/lessons/` as one line, not into a skill.
