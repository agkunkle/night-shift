#!/usr/bin/env bash
# Make the worker-side enroll skill available in every Claude session.
# The manager-side skills stay project-local in .claude/skills/ so that only a session
# started in this directory can run them.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.claude/skills"
ln -sfn "$here/skills/night-shift-enroll" "$HOME/.claude/skills/night-shift-enroll"
echo "linked: ~/.claude/skills/night-shift-enroll -> $here/skills/night-shift-enroll"
