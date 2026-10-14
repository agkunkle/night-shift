# night_shift

A Claude session that acts as a **night manager**. While you are away (one night or a whole
weekend), it supervises your interactive Claude sessions. It wakes every 20 minutes, finds
enrolled workers that are idle, and sends each one a concrete next step, a redirect, backlog
work, or a "park it" instruction. In the morning it writes one report.

It does not use tmux or send-keys. It uses Claude Code's cross-session `ListAgents` and
`SendMessage`.

```
                   ┌───────────────────────────────┐
                   │ night-manager  (night_shift/) │
                   │ cron: cycle every 20 min,     │
                   │       end at shift end        │
                   └─┬────────────┬─────────────┬──┘
       ListAgents +  │            │ SendMessage │ writes
       peek.py       │            │ (idle only) │
       (read-only)   ▼            ▼             ▼
             ┌────────────┐ ┌────────────┐  state/ledger.md
             │ worker A   │ │ worker B   │  state/reports/<date>.md
             │ (enrolled) │ │ (enrolled) │
             └────────────┘ └────────────┘
```

## Use

One time: `./install.sh`. This links the worker-side `night-shift-enroll` skill into
`~/.claude/skills/`.

Each evening:

1. In each session that should continue: `/night-shift-enroll`. The worker drafts its charter
   from its own context. You approve or edit it.
2. In a terminal: `cd night_shift && claude`. Then `/rename night-manager`.
3. `/night-shift-start`, or `/night-shift-start until Monday 07:00` for a weekend.
4. Leave. All sessions must stay open in **auto mode**. Windows must not sleep.

Back early? Tell the manager "I'm back". It runs `/night-shift-end`.

## Files

| Path | What |
|---|---|
| `AGENTS.md` | Manager persona and rules: classification, QA checks, backlog, authority. |
| `charter_template.md` | Per-worker charter format. |
| `skills/night-shift-enroll/` | Worker side. Installed globally by `install.sh`. |
| `.claude/skills/night-shift-{start,cycle,end}/` | Manager side. Only loads in this directory. |
| `peek.py` | Read-only evidence: git activity, tamper scan, transcript tail, repeated errors. |
| `tests/` | `python3 -m pytest tests` |
| `state/` | Runtime state (git-ignored). |

## Design decisions

- **Opt-in enrollment.** `ListAgents` shows every local session. Only enrolled sessions get
  messages.
- **The worker writes its own charter.** It has the daytime context. The manager does not.
- **Manager-initiated only.** Workers do not message the manager. The manager reads their
  transcripts. Idle gaps of up to 20 minutes are acceptable.
- **No Stop hook.** Daytime sessions behave normally.
- **The manager is read-only in worker projects.** This avoids collisions with the worker.
- **Evidence over self-report.** `peek.py` checks commits, repeated errors, and diff patterns
  such as skipped tests and `|| true`, not only what the worker says.

## Open questions (to check in experiments)

- Does a cron prompt of `/night-shift-cycle` invoke the skill reliably?
- How well does `peek.py` find the right transcript when two sessions share one project
  directory? (Enrollment records the transcript path to avoid this.)
- Does the manager stay coherent through many compactions on a weekend shift?

## License

MIT. See `LICENSE`.
