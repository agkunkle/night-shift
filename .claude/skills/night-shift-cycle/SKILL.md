---
name: night-shift-cycle
description: One night-manager supervision cycle - find idle enrolled workers, assess them with evidence, and send each one a concrete next step, a redirect, backlog work, or a park instruction. Runs every 20 minutes during the night shift.
---

# Night shift cycle

1. **Refresh.** Re-read `AGENTS.md` sections "Classify", "QA", and "Backlog" if they are not
   clearly in your context. Read `state/shift.md`, every charter in `state/roster/`, and the
   last ~60 lines of `state/ledger.md`.
   - **Missed end?** If the local time is past `end` in `state/shift.md` and no final report
     exists for this shift, a usage limit probably made the scheduled end fail. Run
     `/night-shift-end` now and stop this cycle.
   - **Gap?** If more than 40 minutes passed since the last ledger entry, log the gap (see
     `AGENTS.md`, "Long shifts").
2. **List.** Call `ListAgents`. Match each charter to a live session by `session` name. If the
   name is not found, match by `cwd`.
3. **Wrap-up window.** If the local time is at or after `wrap_up` in `state/shift.md`: send
   every `active` or `parked` worker (busy or idle) the wrap-up message below, set its status
   to `wrapped`, log it, and
   skip steps 4-6 for it. Messages to busy workers wait in a queue, so that is safe.

   > Night shift is ending. Finish your current step, commit WIP to your working branch (never
   > main), and end with a handoff summary: done / in progress / blocked / next steps.

4. **For each charter with `status: active`:**
   - Not live → set `status: gone`, log it.
   - `[busy]` → log `busy` with no action. Do not message busy workers.
   - `[idle]` → assess (step 5).
   - `parked` workers: send backlog work only if the ledger shows they finished the last item.
     Never send them back to the blocker.
5. **Assess an idle worker.**
   - Run `python3 peek.py --cwd <cwd> --transcript <transcript> --since <enrolled>`.
   - Read the worker's last status in the peek output and the worker's ledger history.
   - Classify as stalled / stuck / blocked / done / limited, with the table in `AGENTS.md`.
   - **limited → send the resume message** and move on. Check this first.
   - **Any `tamper` flags, or a "done" claim → run the QA checklist** before you accept it.
   - **Stuck → enter the project** (`AGENTS.md`, "Enter the project") before you write the
     redirect.
   - Count redirects on the current problem from the ledger. At 3 without progress → blocked.
6. **Act.** Send one `SendMessage` to the worker's session name:
   - stalled → answer from the charter, or give the next step.
   - stuck → the concrete redirect.
   - blocked → "Write your current state, what you tried, and what you need from the user into
     your end-of-turn status. Then take this backlog item: <item>." Set `status: parked`.
   - done → next backlog item.
   - QA failure → "Revert <hack> and fix the real cause, or park it with notes."
   If the tool result shows the message was held or refused, log it as a blocker for the report.
7. **Log.** Append one ledger entry per worker, in the format from `AGENTS.md`.
8. **Finish quietly.** Do not summarize to the chat. The ledger is the record.
