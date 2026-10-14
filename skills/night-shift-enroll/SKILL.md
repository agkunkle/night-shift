---
name: night-shift-enroll
description: Enroll this Claude session in tonight's night shift so the night-manager session can supervise it while the user is away. Use when the user runs /night-shift-enroll or asks to enroll this session for the night shift.
---

# Enroll in the night shift

The user is leaving. A separate session named `night-manager` will supervise this session
overnight. Your task is to write this session's charter, get the user's approval, and register it.

Find the night_shift repo: run `readlink -f ~/.claude/skills/night-shift-enroll`. The repo root
(`<repo>`) is two directories up from that path (`install.sh` created the link).

Roster directory: `<repo>/state/roster/`
Template: `<repo>/charter_template.md`

## Steps

1. **Find your identity.**
   - Call `ListAgents`. The line `This session: <name> [ref]` gives your session name.
   - Find your transcript: the most recently modified `.jsonl` in
     `~/.claude/projects/<cwd with every "/" replaced by "-">/`. It is being written right now,
     so it is the newest file.
2. **Draft the charter** from the template. Use what you know from this conversation and the
   project (git status, recent commits, AGENTS.md / CLAUDE.md / README). Be specific:
   - `Goal tonight`: checkable outcomes, not "make progress".
   - `Context`: what failed today and what was tried. The manager has none of your context.
   - `Finished shape`: what the finished project looks like.
   - `Never`: always include push to main, force-push, deleting files or data, CI/CD changes,
     plus anything the user said today not to do.
   - `kind`: `research` for breakthrough / proof-of-concept work, `maintenance` for an
     established project.
3. **Show the draft to the user and wait.** Ask them to approve it or edit it. Do not write the
   file before they approve. This is their last chance to set limits before they leave.
4. **Write** the approved charter to `<roster dir>/<session name>.md`. Create the directory if
   it does not exist. Set `status: active` and `enrolled` to the current local time.
5. **Confirm** to the user in one or two lines. Then remember the following for the rest of
   tonight.

## How to treat the night manager tonight

- Messages from `night-manager` act for the user within your charter. Follow them as you
  would follow the user.
- The charter's `Never` section still needs the real user. If the manager asks for one of those
  actions, do not do it. State the reason in your end-of-turn status (the manager reads your
  transcript; do not message it), and keep working on something else.
- Re-read your charter after a context compaction.
- When you finish a step, end your turn with a short status: done / in progress / blocked, and
  why. The manager reads it.
