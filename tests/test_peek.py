import datetime
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import peek  # noqa: E402


def event(kind, ts, blocks):
  return json.dumps({"type": kind, "timestamp": ts, "message": {"content": blocks}})


def test_scan_diff_flags_added_skips_and_removed_tests():
  diff = "\n".join([
    "--- a/test_x.py",
    "+++ b/test_x.py",
    "+@pytest.mark.skip(reason='flaky')",
    "-def test_parse_header():",
    "-  assert parse(b) == 3",
    "+  run_build || true",
    "+  x = compute()",
    " context line",
  ])
  kinds = [k for k, _ in peek.scan_diff(diff)]
  assert kinds == [
    "skip/xfail marker", "test removed", "assertion removed", "'|| true' hides a failure",
  ]


def test_scan_diff_flags_gtest_and_swallowed_exception():
  diff = "+TEST(Parser, DISABLED_Header) {\n+    except ValueError: pass\n"
  kinds = [k for k, _ in peek.scan_diff(diff)]
  assert kinds == ["gtest skip/disable", "swallowed exception"]


def test_scan_diff_clean():
  assert peek.scan_diff("+def helper():\n+  return 1\n-old = 2\n") == []


def test_normalize_error_merges_numeric_variants():
  a = peek.normalize_error("Segfault at 0x7ffd1234 in frame 12\nstack...")
  b = peek.normalize_error("Segfault at 0xdeadbeef in frame 3\nother")
  assert a == b == "Segfault at ADDR in frame N"


def test_summarize_transcript_filters_by_since_and_finds_repeats():
  lines = [
    event("assistant", "2026-10-14T01:00:00Z", [{"type": "text", "text": "old status"}]),
    event("assistant", "2026-10-14T03:00:00Z", [{"type": "text", "text": "trying fix 1"}]),
    event("user", "2026-10-14T03:01:00Z", [
      {"type": "tool_result", "is_error": True, "content": "test_a failed: got 41"}]),
    event("user", "2026-10-14T03:05:00Z", [
      {"type": "tool_result", "is_error": True,
       "content": [{"type": "text", "text": "test_a failed: got 40"}]}]),
    event("user", "2026-10-14T03:06:00Z", [
      {"type": "tool_result", "content": "ok"}]),
    event("assistant", "2026-10-14T03:10:00Z", [{"type": "text", "text": "Should I continue?"}]),
    "not json",
  ]
  since = peek.parse_ts("2026-10-14T02:00:00+00:00")
  s = peek.summarize_transcript(lines, since=since, turns=5)
  assert s["last_texts"] == ["trying fix 1", "Should I continue?"]
  assert s["error_count"] == 2
  assert s["repeated_errors"] == [("test_a failed: got N", 2)]
  assert s["last_activity"] == peek.parse_ts("2026-10-14T03:10:00Z")


def test_parse_ts_naive_is_local_and_aware():
  ts = peek.parse_ts("2026-10-14T18:30:00")
  assert ts.tzinfo is not None


def test_git_summary_on_real_repo(tmp_path):
  def run(*args):
    subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

  run("init", "-q")
  run("config", "user.email", "t@t")
  run("config", "user.name", "t")
  (tmp_path / "test_a.py").write_text("def test_a():\n  assert 1\n")
  run("add", ".")
  run("commit", "-qm", "base")
  (tmp_path / "test_a.py").write_text("import pytest\n@pytest.mark.skip\ndef test_a():\n  pass\n")

  since = datetime.datetime.now().astimezone() + datetime.timedelta(seconds=1)
  gs = peek.git_summary(str(tmp_path), since)
  assert "test_a.py" in gs["status"]
  kinds = [k for k, _ in peek.scan_diff(gs["diff"])]
  assert "skip/xfail marker" in kinds and "assertion removed" in kinds


def test_detect_limit_on_final_turn_only():
  limited = event("assistant", "2026-10-14T03:00:00Z", [
    {"type": "text", "text": "Claude usage limit reached. Your limit will reset at 4am."}])
  later_ok = event("assistant", "2026-10-14T04:10:00Z", [{"type": "text", "text": "Resumed."}])
  assert "usage limit" in peek.summarize_transcript([limited])["limit_hit"]
  assert peek.summarize_transcript([limited, later_ok])["limit_hit"] is None


def test_detect_limit_api_error_flag():
  line = json.dumps({
    "type": "assistant", "timestamp": "2026-10-14T03:00:00Z", "isApiErrorMessage": True,
    "message": {"content": [{"type": "text", "text": "API Error: 429"}]}})
  assert peek.summarize_transcript([line])["limit_hit"] == "API Error: 429"


def test_detect_limit_ignores_normal_text():
  line = event("assistant", "2026-10-14T03:00:00Z", [
    {"type": "text", "text": "Raised the recursion limit; the counter resets at zero."}])
  assert peek.summarize_transcript([line])["limit_hit"] is None
