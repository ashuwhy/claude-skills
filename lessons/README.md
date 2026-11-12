# lessons

Dated incident logs, one file per app, one line per incident with the rule it left in a skill. No skill loads them; they are the evidence for when a rule needs re-judging.

The logs themselves are gitignored. They name live apps, dates and the security holes those apps had, which is not something to publish. Keep each next to this file on your own machine, in this shape:

| Date | What happened | Rule it left |
|---|---|---|
| 2026-08-21 | `cron.job_run_details` grew to 134MB of a 147MB database and Postgres refused connections | supabase-backend: purge job beside the first cron job |
