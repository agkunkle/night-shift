---
name: night-shift-start
description: Start the night shift as the night manager - check the roster, schedule the 20-minute supervision cycle and the 05:30 end, then run the first cycle. Use when the user runs /night-shift-start or says to start the night shift.
---

# Start the night shift

1. **Load the persona.** Read `AGENTS.md` in this directory in full. Follow it all night.
2. **Check your name.** Call `ListAgents`. If this session is not named `night-manager`, tell the
   user to run `/rename night-manager` and stop here.
3. **Check state.**
   - Create `state/roster/`, `state/reports/`, `state/archive/` if missing.
   - If `state/ledger.md` exists from an earlier night, ask the user whether to archive it
     (move it to `state/archive/<its date>/`). Do not delete it.
4. **Check the roster against live sessions.** Read every charter in `state/roster/`. Show the
   user one table:

   | session | kind | status | live? | goal (short) |

   Also list live sessions that are **not** enrolled, so the user can enroll any they forgot.
   Warn about charters whose session is not live.
5. **Remind the user** (one short list):
   - Windows must not sleep, and WSL must stay up overnight.
   - All sessions must stay open, in auto mode.
6. **Set the shift end.** The user may give an end time as an argument, e.g.
   `/night-shift-start until Monday 07:00`. Default: 05:30 on the next morning (today if it is
   already after midnight). Shifts longer than 7 days are not supported (`CronCreate` recurring
   jobs expire after 7 days). Write `state/shift.md`:

   ```
   start: <ISO local time>
   end: <ISO local time>
   wrap_up: <end minus 30 minutes>
   multi_day: <true if end is more than 24 h away>
   ```

7. **Schedule** with `CronCreate` (all jobs live only in this session):
   - Cycle: cron `7,27,47 * * * *`, recurring, prompt `/night-shift-cycle`.
   - End: one-shot at `end`, cron `<min> <hour> <dom> <month> *`, recurring false,
     prompt `/night-shift-end`.
   - If `multi_day`: daily digest, cron `30 5 * * *`, recurring, prompt
     `/night-shift-end digest`.
   Tell the user the actual next run times that `CronCreate` returns.
8. **Start the ledger.** Append `## Shift <start> → <end>` and a line with the roster.
9. **Run the first cycle now**: follow `/night-shift-cycle`.
