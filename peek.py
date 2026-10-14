#!/usr/bin/env python3
"""Read-only evidence gatherer for the night manager.

Prints a markdown summary of one worker: git activity since enrollment, a test-tampering scan
of the diff, and the tail of the worker's transcript (last status, tool errors, repeated errors).

Usage: python3 peek.py --cwd DIR --transcript FILE [--since ISO] [--turns N]
"""

import argparse
import collections
import datetime
import json
import re
import subprocess

# Added lines that often mean "make the test pass" instead of "fix the bug".
ADDED_TAMPER_PATTERNS = [
  (r"@pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|@unittest\.skip", "skip/xfail marker"),
  (r"\bGTEST_SKIP\b|\bDISABLED_\w+", "gtest skip/disable"),
  (r"\b(it|test|describe)\.skip\(|\bx(it|describe)\(", "js test skip"),
  (r"\|\|\s*true\b", "'|| true' hides a failure"),
  (r"except(\s+\w+(\s+as\s+\w+)?)?\s*:\s*pass\b", "swallowed exception"),
  (r"\bif\s+.*\b(TESTING|PYTEST_CURRENT_TEST|UNDER_TEST|IS_TEST)\b", "test-detection branch"),
  (r"\b(HACK|SHIM|WORKAROUND)\b", "hack/shim marker"),
]

# Removed lines that may mean a test or assertion was deleted.
REMOVED_TAMPER_PATTERNS = [
  (r"^\s*def test_\w+|^\s*TEST(_F|_P)?\(|^\s*(it|test)\(", "test removed"),
  (r"\bassert\w*\b|\bEXPECT_\w+\(|\bASSERT_\w+\(|\bexpect\(", "assertion removed"),
]


def parse_ts(text):
  """Parse an ISO timestamp. Naive values are local time. Returns an aware datetime."""
  ts = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
  if ts.tzinfo is None:
    ts = ts.astimezone()
  return ts


def scan_diff(diff_text):
  """Return (kind, line) findings for suspicious added/removed lines in a unified diff."""
  findings = []
  for line in diff_text.splitlines():
    if line.startswith(("+++", "---")):
      continue
    if line.startswith("+"):
      patterns, body = ADDED_TAMPER_PATTERNS, line[1:]
    elif line.startswith("-"):
      patterns, body = REMOVED_TAMPER_PATTERNS, line[1:]
    else:
      continue
    for pattern, kind in patterns:
      if re.search(pattern, body):
        findings.append((kind, line.strip()[:160]))
        break
  return findings


def normalize_error(text):
  """Reduce an error to a stable key so the same failure repeated with new numbers matches."""
  first = next((l for l in text.strip().splitlines() if l.strip()), "")
  first = re.sub(r"0x[0-9a-fA-F]+", "ADDR", first)
  first = re.sub(r"\d+", "N", first)
  return re.sub(r"\s+", " ", first).strip()[:200]


def block_text(content):
  """Flatten tool_result content (str or list of blocks) to text."""
  if isinstance(content, str):
    return content
  if isinstance(content, list):
    return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
  return ""


def summarize_transcript(lines, since=None, turns=5):
  """Summarize transcript JSONL lines. Only events at or after `since` count."""
  last_activity = None
  texts = []
  errors = []
  for raw in lines:
    try:
      event = json.loads(raw)
    except json.JSONDecodeError:
      continue
    if event.get("type") not in ("user", "assistant") or "timestamp" not in event:
      continue
    ts = parse_ts(event["timestamp"])
    if since and ts < since:
      continue
    last_activity = ts
    content = event.get("message", {}).get("content")
    if not isinstance(content, list):
      continue
    for block in content:
      if block.get("type") == "text" and event["type"] == "assistant" and block["text"].strip():
        texts.append(block["text"].strip())
      elif block.get("type") == "tool_result" and block.get("is_error"):
        errors.append(block_text(block.get("content")))
  counts = collections.Counter(normalize_error(e) for e in errors if e.strip())
  return {
    "last_activity": last_activity,
    "last_texts": texts[-turns:],
    "error_count": len(errors),
    "repeated_errors": [(k, n) for k, n in counts.most_common() if n >= 2],
  }


def git(cwd, *args):
  result = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
  return result.stdout.rstrip() if result.returncode == 0 else ""


def git_summary(cwd, since):
  """Commits since `since`, working tree state, and the diff since the last pre-`since` commit."""
  since_arg = since.isoformat() if since else "12 hours ago"
  base = git(cwd, "rev-list", "-1", f"--before={since_arg}", "HEAD") or "HEAD"
  return {
    "branch": git(cwd, "rev-parse", "--abbrev-ref", "HEAD"),
    "commits": git(cwd, "log", f"--since={since_arg}", "--oneline"),
    "status": git(cwd, "status", "--short"),
    "diff_stat": git(cwd, "diff", "--stat", base),
    "diff": git(cwd, "diff", base),
  }


def render(cwd, since, gs, ts):
  now = datetime.datetime.now().astimezone()
  out = [f"# peek: {cwd}", ""]
  out += ["## git", f"branch: {gs['branch'] or '?'}", "", "commits since enrollment:"]
  out += [gs["commits"] or "(none)", "", "uncommitted:", gs["status"] or "(clean)", ""]
  out += ["diff stat since enrollment:", gs["diff_stat"] or "(none)", ""]

  findings = scan_diff(gs["diff"])
  out += [f"## tamper scan: {len(findings)} flag(s)"]
  out += [f"- [{kind}] `{line}`" for kind, line in findings] or ["(clean)"]
  out += [""]

  out += ["## transcript"]
  if ts["last_activity"]:
    idle_min = int((now - ts["last_activity"]).total_seconds() // 60)
    out += [f"last activity: {ts['last_activity'].astimezone():%H:%M} ({idle_min} min ago)"]
  out += [f"tool errors since enrollment: {ts['error_count']}"]
  if ts["repeated_errors"]:
    out += ["repeated errors (possible loop):"]
    out += [f"- x{n}: `{k}`" for k, n in ts["repeated_errors"][:5]]
  out += ["", "recent assistant text (oldest first; last item = latest status):"]
  for text in ts["last_texts"]:
    out += ["---", text[:1500]]
  return "\n".join(out)


def main():
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument("--cwd", required=True, help="worker project directory")
  parser.add_argument("--transcript", required=True, help="worker transcript .jsonl")
  parser.add_argument("--since", help="ISO time, usually the charter's `enrolled`")
  parser.add_argument("--turns", type=int, default=5, help="assistant text blocks to show")
  args = parser.parse_args()

  since = parse_ts(args.since) if args.since else None
  with open(args.transcript, encoding="utf-8") as f:
    ts = summarize_transcript(f, since, args.turns)
  print(render(args.cwd, since, git_summary(args.cwd, since), ts))


if __name__ == "__main__":
  main()
