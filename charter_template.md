---
session: <session name from ListAgents, e.g. youtube-videos-1c>
cwd: <absolute project path>
transcript: <absolute path to the session's .jsonl transcript>
enrolled: <ISO timestamp, e.g. 2026-10-14T18:30:00>
kind: <research | maintenance>
status: active   # active | parked | wrapped | gone  (the manager updates this)
---

## Goal tonight
<What counts as progress by morning. Concrete and checkable.>

## Context
<Where things stand now: what works, what failed today, what was tried, open hypotheses.>

## Finished shape
<What the finished project looks like: artifacts, supported devices/platforms, test suite
state, docs. The manager uses this to judge "done" and to steer.>

## How to check progress
<Commands and files: test command, log locations, benchmark, expected outputs.>

## Allowed without asking
<Actions the worker may take tonight, e.g. edit src/, add tests, commit to branch X.>

## Never
<Actions that need the real user, e.g. push to main, delete data, change CI, spend money.>

## Abandon if
<Conditions that mean "stop and wait for the user", e.g. approach needs a kernel rebuild.>

## Backlog
<Project-specific mechanical tasks for when the goal is done or blocked. Optional; the
manager also has a default backlog.>
