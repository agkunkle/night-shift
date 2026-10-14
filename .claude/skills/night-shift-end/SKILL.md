---
name: night-shift-end
description: End the night shift and write the morning report, or (with the "digest" argument) write a daily digest during a multi-day shift. Use at the scheduled shift end, or when the user says "I'm back", "I'm here", "end the night shift", or similar.
---

# End the night shift

## Digest mode (`/night-shift-end digest`)

For multi-day shifts. Do **not** stop the schedule, send wrap-ups, or archive. If the shift
`end` in `state/shift.md` is less than 2 hours away, skip the digest (the final report follows).
Otherwise do steps 3-4 below for the last 24 hours only, and write
`state/reports/<YYYY-MM-DD>-digest.md`. Then stop.

## Full end

1. **Stop the schedule.** `CronList`, then `CronDelete` every night-shift job (the cycle, the
   daily digest, and the scheduled end if the user ended early).
2. **Wrap up.** Send the wrap-up message from `/night-shift-cycle` step 3 to every worker whose
   status is not yet `wrapped` or `gone`. If the user ended early, start that message with:
   "The user is back."
3. **Gather.** For each charter: run `peek.py` (since `enrolled`), read its ledger entries, and
   read its latest end-of-turn status. A worker may still be busy with wrap-up; report its
   latest state and say so.
4. **Write `state/reports/<YYYY-MM-DD>.md`.** Easy to read in two minutes:

   ```
   # Night shift report — <date>
   <one-sentence summary of the night>

   ## Needs you
   - <decisions, blockers, QA problems; one line each, with project name>

   ## At a glance
   | project | goal | outcome | commits | needs you? |

   ## Per project
   ### <session>
   - Done: ...
   - In progress: ...
   - Blocked / parked: ... (why, what was tried)
   - QA: <tamper flags and how they were resolved, or "clean">
   - Manager interventions: <count>; which helped

   ## Manager notes
   <what worked and what did not, for tuning the night shift>
   ```

   "Needs you" comes first. Report failures as clearly as successes. Do not pad.
   For a multi-day shift, add a short `## Day by day` section after "At a glance", built from
   the digests.
5. **Archive.** Move `state/roster/*.md`, `state/ledger.md`, and `state/shift.md` to
   `state/archive/<date>/`.
6. **Show the report.** Run `code -r -g state/reports/<date>.md`. If the user is present, give a
   three-line summary in chat and point to the file.
