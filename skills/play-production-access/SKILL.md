---
name: play-production-access
description: Google Play production access for a new personal developer account - the closed test, recruiting testers, the evidence Google reads, the application form, and review rejections. Use when planning a closed test, applying for production, or answering a Play rejection.
---

# Getting Play production access

Play's rules change. Read the current requirement in Play Console help before planning anything. *(checked 2026-10: a personal account created after Nov 2023 needs 12+ testers opted into a closed test for 14 continuous days, then an approved application.)* Everything below is how to pass that review, with the reason for each step so it can be adapted when the form changes.

The one lesson that matters most: **Google judges installs and engagement, not opt-ins.** An opt-in is a click on a link. Applying on the opt-in count while Play's own install report shows a handful of devices gets refused, twice in my case.

## 1. Set up the closed test

- A named closed track. Internal testing does not count.
- Crash reporting and per-device analytics in the very first tester build (see `product-analytics`). Play vitals stays empty with a small audience, so my own data is the only evidence I will have.

Done when: a build is on the closed track and one tester outside my own devices shows up in analytics.

## 2. Recruit early, and twice what's needed

Start the week the developer account exists. Real users first, through channels I already have. Expect fewer than half to stay active. If the count is short, paid tester services exist; declare them in the application, since hiding them reads worse than using them.

Done when: the Console Dashboard shows the required testers and the counter running.

## 3. Run the window like a release cycle

The reviewer wants to see testing change the app.

- A Play build every one or two days, each with a release note. OTA updates are invisible to Google.
- Every piece of tester feedback becomes a dated change. Reply to every written review in Testing > Feedback.
- Count tester devices daily from analytics, excluding my own, and note who took an update from Play.

Done when: every closed-test check is green and "Apply for production" is live.

## 4. Write the application

[questions.md](questions.md) has what each question checks and how to answer it. Every number comes from a query, the track list (`play.py tracks`) or git, refreshed on the day. Write full answers in a repo doc with their sources first, then cut to the Console's character limit.

Done when: every answer fits and every figure traces to a source.

## 5. Before submitting

- [ ] OAuth consent screen is "In production", or the reviewer cannot sign in with Google.
- [ ] App access gives the reviewer a way in: an email and password account made for review, onboarding done. A shared Gmail account fails because Google's own verification prompt fires from an unfamiliar device and country.
- [ ] Nothing in the app, listing or screenshots claims something the app lacks: user counts, empty categories, features on a roadmap, prices the app no longer charges.
- [ ] Privacy policy and the Data safety form describe the same data. Any personal field in onboarding says why it is asked for.
- [ ] The account deletion page mails a domain I actually read.
- [ ] No real user's name or data in screenshots.
- [ ] Pre-launch report opened; any crash it lists is fixed and named in the answers.

## Rejections

- **Access blocked by MFA**: fix the review account, not the app.
- **Crash on launch**: test the exact Play build on a real low-end phone before submitting. Render paths that assume data exists (`rows.map` on undefined) and throws inside startup effects are the usual causes.
- **Policy flag on orientation or large screens**: see `expo-release`, First store build.
- While a rejected update is pending, commit edits with `changesNotSentForReview=true` and send everything for review once.
