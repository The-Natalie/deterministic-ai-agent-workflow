#!/usr/bin/env python3
"""Automatic conversation logging for this project (Muse AND Claude Code).

Reads the native session logs of whichever coding agent you use here -- Muse
(~/.local/share/muse/sessions) and/or Claude Code (~/.claude/projects) -- and
appends the user-visible conversation (your prompts and the agent's replies)
to per-session Markdown files in <project>/conversation-log/. Sessions of
other projects are ignored. Entries are labelled "You", "Muse" or "Claude".

Commands:
    conversation-log.py start    One-time setup: start the background logger now
                                 and on every login (macOS LaunchAgent)
    conversation-log.py stop     Stop the background logger and remove it
    conversation-log.py status   Show whether the background logger is running
    conversation-log.py once     Single pass: log everything so far, then exit
    conversation-log.py watch    Run in the foreground, checking every --interval
                                 seconds (what the background logger runs)

State (per-session checkpoints) lives in conversation-log/, so re-runs and
restarts never duplicate entries. Muse and Claude each keep their own state
file there.

Safety: the logging passes only READ the agents' session logs. They never
modify, move, or delete them, use no network, and make no API calls, so they
cost no tokens and cannot interfere with your agent. (start/stop/status call
launchctl to manage the background service; nothing else runs subprocesses.)

Privacy: logs contain everything typed, including any secrets. Keep
conversation-log/ out of git (the starter's .gitignore already does).

Schema note: the Muse parser was validated against Muse Code 1.4.14 and the
Claude parser against current Claude Code transcripts. Both formats are
undocumented and may change; unknown shapes are skipped with a stderr
warning, never crash the run.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime

STATE_VERSION = 1
_INDEX_WARNED = False


def default_sessions_root():
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    return os.path.join(base, "muse", "sessions")


def default_project_root():
    # Script lives at <project>/tools/conversation-log.py
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_index_db():
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    return os.path.join(base, "muse", "session-index.db")


def read_session_names(index_db, session_ids):
    """Return {session_id: (name, revision)} from Muse's session index.

    Reads the SQLite index read-only. Prefers the canonical session_name
    column with fallback to logged_session_name (the populated one in
    1.4.14). Returns {} on any failure -- missing/locked database or an
    unexpected schema -- so callers degrade to UUID-only logging. Warns
    once per process; never raises.
    """
    global _INDEX_WARNED
    if not session_ids:
        return {}
    try:
        con = sqlite3.connect(f"file:{index_db}?mode=ro", uri=True, timeout=5)
        try:
            rows = con.execute(
                "SELECT session_id, "
                "COALESCE(session_name, logged_session_name), "
                "COALESCE(session_name_revision, logged_session_name_revision) "
                f"FROM sessions WHERE session_id IN "
                f"({','.join('?' for _ in session_ids)})",
                list(session_ids),
            ).fetchall()
        finally:
            con.close()
    except (sqlite3.Error, OSError) as exc:
        if not _INDEX_WARNED:
            print(
                f"warning: session index unavailable ({exc}); logging UUID-only",
                file=sys.stderr,
            )
            _INDEX_WARNED = True
        return {}
    _INDEX_WARNED = False
    return {sid: (name, rev) for sid, name, rev in rows if name}


def iter_inner_records(line):
    """Yield parsed records from one JSONL line, unwrapping framed children.

    Most lines are records themselves. Some lines are retained_frame envelopes
    whose children carry their record as an embedded JSON string (record_json).
    Raises ValueError on malformed JSON (caller treats as a torn write and
    retries the line on the next pass).
    """
    top = json.loads(line)
    if isinstance(top, dict) and "payload_type" in top:
        yield top
        return
    for child in top.get("children", []) if isinstance(top, dict) else []:
        if isinstance(child, dict) and isinstance(child.get("record_json"), str):
            yield json.loads(child["record_json"])


def find_workspace_root(path, max_records=500):
    """Return the workspace_root recorded in a session log, or None.

    The marker lives in a runtime.session.metadata record near the start of
    the log. Returns None when absent (e.g. a brand-new session whose startup
    records are not yet flushed) -- callers must re-check later.
    """
    checked = 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records = list(iter_inner_records(line))
                except ValueError:
                    continue  # torn write; stop scanning, not fatal
                for rec in records:
                    if not isinstance(rec, dict):
                        continue
                    payload = rec.get("payload")
                    if not isinstance(payload, dict):
                        continue
                    record = payload.get("record")
                    if isinstance(record, dict) and record.get("workspace_root"):
                        return record["workspace_root"]
                    checked += 1
                    if checked >= max_records:
                        return None
    except (OSError, UnicodeDecodeError):
        return None
    return None


def discover_sessions(sessions_root, project_root, state):
    """Return {session_id: info} for project sessions, updating cached state.

    Sessions whose workspace does not match are cached in state["ignored"] so
    they are never scanned again. Sessions with no workspace marker yet are
    re-checked on every pass (they may be newly started sessions).
    """
    project_root = os.path.realpath(project_root)
    ignored = state.setdefault("ignored", {})
    found = {}
    pattern = os.path.join(sessions_root, "*", "*", "*", "*", "session.jsonl")
    for path in glob.glob(pattern):
        session_id = os.path.basename(os.path.dirname(path))
        if session_id in ignored:
            continue
        cached = state.get("sessions", {}).get(session_id)
        if cached is not None:
            found[session_id] = {"path": path, "workspace_root": cached["workspace_root"]}
            continue
        root = find_workspace_root(path)
        if root is None:
            continue  # undecided; re-check next pass
        if os.path.realpath(root) == project_root:
            # Date shards: .../YYYY/MM/DD/<session-id>/session.jsonl
            parts = path.split(os.sep)
            date = "-".join(parts[-5:-2]) if len(parts) >= 5 else "unknown-date"
            found[session_id] = {"path": path, "workspace_root": root, "date": date}
        else:
            ignored[session_id] = root
    return found


def extract_entries(path, after_sequence):
    """Yield (sequence, speaker, text, recorded_at) for new conversation records.

    Only user-visible conversation is extracted:
      user:      run "started" prompt (non-empty), else the run's
                 "user_prompt_display" text (even a placeholder like "[Image 1]",
                 which at least records that a user turn occurred), plus
                 "user_steer" inbox items queued mid-run.
      assistant: "assistant_message_committed" text.
    Tool calls/results, encrypted reasoning blobs, background inbox items, and
    empty internal child-run prompts are intentionally excluded.

    Returns (entries, max_sequence). Sequence numbers are the dedup
    checkpoint: callers persist the max and pass it back as after_sequence.
    On a malformed trailing line (torn write while Muse is appending),
    scanning stops before that line; already-yielded entries still carry
    their sequences, so nothing is lost or duplicated.
    """
    entries = []
    run_has_prompt = {}  # run_id -> bool (non-empty started prompt seen)
    pending_runs = set()  # run_ids with started record seen
    max_seq = after_sequence
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    records = list(iter_inner_records(line.strip()))
                except ValueError:
                    break  # torn trailing write; retry it next pass
                for rec in records:
                    if not isinstance(rec, dict):
                        continue
                    seq = rec.get("sequence")
                    if not isinstance(seq, int):
                        continue
                    if seq > max_seq:
                        max_seq = seq
                    if seq <= after_sequence:
                        continue
                    payload = rec.get("payload")
                    if not isinstance(payload, dict):
                        continue
                    event = payload.get("event")
                    if not isinstance(event, dict):
                        continue
                    kind = event.get("kind")
                    run_id = payload.get("run_id")
                    ts = rec.get("recorded_at")
                    if kind == "started" and payload.get("kind") == "run":
                        pending_runs.add(run_id)
                        prompt = event.get("prompt")
                        if isinstance(prompt, str) and prompt:
                            run_has_prompt[run_id] = True
                            entries.append((seq, "user", prompt, ts))
                        # Empty prompt = internal child run, not user speech:
                        # skipped (counted by caller via skipped_empty).
                    elif kind == "user_prompt_display":
                        if run_id not in pending_runs or not run_has_prompt.get(run_id):
                            text = event.get("prompt")
                            if isinstance(text, str) and text:
                                run_has_prompt[run_id] = True
                                entries.append((seq, "user", text, ts))
                        # Else: full text already captured from started.prompt.
                    elif kind == "inbox_item_queued":
                        source = event.get("source")
                        origin = source.get("source") if isinstance(source, dict) else None
                        if origin == "user_steer":
                            text = None
                            inner = event.get("payload")
                            if isinstance(inner, dict) and isinstance(
                                inner.get("prompt"), str
                            ):
                                text = inner["prompt"]
                            elif isinstance(event.get("body"), str):
                                text = event["body"]
                            if text:
                                entries.append((seq, "user", text, ts))
                        # Other origins (background/scheduled deliveries) are
                        # not user speech and are excluded.
                    elif kind == "assistant_message_committed":
                        text = event.get("text")
                        if isinstance(text, str) and text:
                            entries.append((seq, "assistant", text, ts))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        return entries, after_sequence
    entries.sort(key=lambda e: e[0])
    return entries, max_seq


def format_timestamp(recorded_at):
    if isinstance(recorded_at, (int, float)):
        try:
            return datetime.fromtimestamp(recorded_at / 1e6).strftime("%Y-%m-%d %H:%M:%S")
        except (OverflowError, OSError, ValueError):
            pass
    return "unknown time"


def format_entry(speaker, text, recorded_at):
    label = "You" if speaker == "user" else "Muse"
    body = text if text.endswith("\n") else text + "\n"
    return f"---\n## {label} \u00b7 {format_timestamp(recorded_at)}\n\n{body}\n"


def load_state(state_path):
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        if isinstance(state, dict) and state.get("version") == STATE_VERSION:
            state.setdefault("sessions", {})
            state.setdefault("ignored", {})
            return state
    except (OSError, ValueError):
        pass
    return {"version": STATE_VERSION, "sessions": {}, "ignored": {}}


def save_state(state_path, state):
    tmp = state_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, state_path)


def ensure_header_name(log_path, name):
    """Sync the '- Session name:' header line. Returns True if changed."""
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    marker = "- Session name:"
    for i, line in enumerate(lines):
        if line.startswith(marker):
            if line.rstrip("\n") == f"{marker} {name}":
                return False
            lines[i] = f"{marker} {name}\n"
            break
    else:
        for i, line in enumerate(lines):
            if line.startswith("- Session ID:"):
                lines.insert(i + 1, f"{marker} {name}\n")
                break
        else:
            return False  # unexpected header shape; leave untouched
    with open(log_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True


def format_rename_note(old, new, stamp):
    return f"---\n*Session renamed: `{old}` \u2192 `{new}` \u00b7 {stamp}*\n\n"


def process_session(session_id, info, log_dir, entry, name_info):
    """Append new entries for one session.

    name_info is a (name, revision) tuple from the session index, or None.
    Returns (conversation_count, rename_note_or_None).
    """
    name, revision = name_info if name_info else (None, None)
    path = info["path"]
    last_seq = entry.get("last_sequence", 0)
    entries, max_seq = extract_entries(path, last_seq)
    entry["last_sequence"] = max_seq
    date = entry.get("date") or info.get("date") or "unknown-date"
    log_name = f"{date}_{session_id}.md"
    log_path = os.path.join(log_dir, log_name)
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(
                f"# Conversation \u2014 {date} (session {session_id[:8]}\u2026)\n"
                f"\n- Session ID: {session_id}\n"
            )
            if name:
                f.write(f"- Session name: {name}\n")
            f.write(
                f"- Date: {date}\n"
                f"- Workspace: {entry.get('workspace_root', '')}\n"
                "- Source: Muse native session log (automatic; do not edit below this line)\n"
                "\n"
            )
    rename_note = None
    if name:
        prev_name = entry.get("current_name")
        if prev_name is None:
            # First sighting: adopt the name, sync the header, no note.
            entry["current_name"] = name
            entry["current_revision"] = revision
            ensure_header_name(log_path, name)
        elif name != prev_name:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rename_note = format_rename_note(prev_name, name, stamp)
            entry.setdefault("name_history", []).append(
                {"from": prev_name, "to": name, "at": stamp}
            )
            entry["current_name"] = name
            entry["current_revision"] = revision
            ensure_header_name(log_path, name)
        elif revision != entry.get("current_revision"):
            entry["current_revision"] = revision  # silent revision-only bump
    if entries or rename_note:
        with open(log_path, "a", encoding="utf-8") as f:
            for seq, speaker, text, ts in entries:
                f.write(format_entry(speaker, text, ts))
                f.flush()
                os.fsync(f.fileno())
            if rename_note:
                f.write(rename_note)
                f.flush()
                os.fsync(f.fileno())
    entry["log_file"] = log_name
    return len(entries), rename_note


def run_once(sessions_root, project_root, log_dir, state_path, index_db, verbose=False):
    os.makedirs(log_dir, exist_ok=True)
    state = load_state(state_path)
    sessions = discover_sessions(sessions_root, project_root, state)
    names = read_session_names(index_db, list(sessions))
    total = 0
    for session_id in sorted(sessions):
        entry = state["sessions"].setdefault(
            session_id,
            {
                "workspace_root": sessions[session_id]["workspace_root"],
                "date": sessions[session_id].get("date", "unknown-date"),
                "last_sequence": 0,
            },
        )
        try:
            count, rename_note = process_session(
                session_id, sessions[session_id], log_dir, entry, names.get(session_id)
            )
        except (OSError, UnicodeDecodeError) as exc:
            print(f"warning: session {session_id[:8]}: {exc}", file=sys.stderr)
            continue
        total += count
        if verbose and (count or rename_note):
            msg = f"session {session_id[:8]}: +{count} entries -> {entry.get('log_file')}"
            if rename_note:
                msg += f" [renamed to {entry.get('current_name')}]"
            print(msg)
        save_state(state_path, state)  # checkpoint after every session
    save_state(state_path, state)
    return total, len(sessions)


# ---------------------------------------------------------------- Claude Code

CLAUDE_STATE_NAME = ".conversation-log-claude-state.json"
_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)


def claude_project_dir(project_root):
    """Claude Code names a project's transcript dir by replacing every
    non-alphanumeric character in its absolute path with '-'."""
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    for candidate in (os.path.abspath(project_root), os.path.realpath(project_root)):
        path = os.path.join(base, re.sub(r"[^A-Za-z0-9]", "-", candidate))
        if os.path.isdir(path):
            return path
    return os.path.join(base, re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(project_root)))


def _claude_text(content):
    if isinstance(content, str):
        return content
    parts = []
    for block in content if isinstance(content, list) else []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif block.get("type") == "image":
            parts.append("[image]")
    return "\n\n".join(parts)


def claude_extract_entry(record):
    """Return (speaker, text, iso_timestamp) for a visible turn, else None.

    Skipped: tool calls/results, thinking blocks, system reminders, subagent
    (sidechain) activity, harness-injected turns, and meta records.
    """
    if not isinstance(record, dict) or record.get("isSidechain") or record.get("isMeta"):
        return None
    kind = record.get("type")
    message = record.get("message")
    if kind not in ("user", "assistant") or not isinstance(message, dict):
        return None
    content = message.get("content")
    if kind == "user":
        if isinstance(content, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        ):
            return None
        origin = record.get("origin")
        if isinstance(origin, dict) and origin.get("kind") not in (None, "human"):
            return None
        text = _REMINDER_RE.sub("", _claude_text(content)).strip()
        speaker = "user"
    else:
        if message.get("model") == "<synthetic>":
            return None
        text = _claude_text(content).strip()
        speaker = "assistant"
    return (speaker, text, record.get("timestamp")) if text else None


def claude_format_entry(speaker, text, iso):
    label = "You" if speaker == "user" else "Claude"
    try:
        stamp = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone().strftime(
            "%Y-%m-%d %H:%M:%S")
    except (AttributeError, ValueError):
        stamp = "unknown time"
    body = text if text.endswith("\n") else text + "\n"
    return f"---\n## {label} \u00b7 {stamp}\n\n{body}\n"


def _claude_read_new_lines(path, offset):
    """Complete new lines since offset; a trailing partial line (a write in
    progress) is left for the next pass."""
    if os.path.getsize(path) < offset:
        offset = 0
    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read()
    end = data.rfind(b"\n")
    if end < 0:
        return [], offset
    chunk = data[: end + 1]
    return chunk.decode("utf-8", errors="replace").splitlines(), offset + len(chunk)


def claude_process_session(session_id, path, project_root, log_dir, entry):
    lines, new_offset = _claude_read_new_lines(path, entry.get("offset", 0))
    entries, title = [], entry.get("title")
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except ValueError:
            print(f"warning: skipping unparseable line in {path}", file=sys.stderr)
            continue
        if isinstance(record, dict) and record.get("type") == "ai-title" and record.get("aiTitle"):
            title = record["aiTitle"]
        found = claude_extract_entry(record)
        if found:
            entries.append(found)
    log_name = entry.get("log_file")
    if not log_name and entries:
        date = (entries[0][2] or "")[:10] or datetime.now().strftime("%Y-%m-%d")
        log_name = f"{date}_{session_id}.md"
        entry["log_file"] = log_name
    if log_name:
        log_path = os.path.join(log_dir, log_name)
        rename_note = None
        if not os.path.exists(log_path):
            date = log_name.split("_", 1)[0]
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(
                    f"# Conversation \u2014 {date} (session {session_id[:8]}\u2026)\n"
                    f"\n- Session ID: {session_id}\n"
                    + (f"- Session name: {title}\n" if title else "")
                    + f"- Date: {date}\n- Workspace: {project_root}\n"
                    "- Source: Claude Code session log (automatic; do not edit below this line)\n\n"
                )
        elif title and title != entry.get("title"):
            ensure_header_name(log_path, title)
            if entry.get("title"):
                stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rename_note = format_rename_note(entry["title"], title, stamp)
        if entries or rename_note:
            with open(log_path, "a", encoding="utf-8") as f:
                for speaker, text, iso in entries:
                    f.write(claude_format_entry(speaker, text, iso))
                if rename_note:
                    f.write(rename_note)
                f.flush()
    entry["title"] = title
    entry["offset"] = new_offset
    return len(entries)


def run_claude_once(project_root, log_dir, verbose=False):
    sessions_dir = claude_project_dir(project_root)
    if not os.path.isdir(sessions_dir):
        return 0, 0  # Claude Code not used for this project (yet)
    os.makedirs(log_dir, exist_ok=True)
    state_path = os.path.join(log_dir, CLAUDE_STATE_NAME)
    state = load_state(state_path)
    total, n = 0, 0
    for name in sorted(os.listdir(sessions_dir)):
        if not name.endswith(".jsonl"):
            continue
        sid = name[: -len(".jsonl")]
        n += 1
        entry = state["sessions"].setdefault(sid, {"offset": 0})
        try:
            count = claude_process_session(
                sid, os.path.join(sessions_dir, name), project_root, log_dir, entry)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"warning: claude session {sid[:8]}: {exc}", file=sys.stderr)
            continue
        total += count
        if verbose and count:
            print(f"claude session {sid[:8]}: +{count} entries -> {entry.get('log_file')}")
        save_state(state_path, state)
    return total, n


# ------------------------------------------------------- run both / background

def run_all(args, verbose=False):
    log_dir = args.log_dir or os.path.join(args.project_root, "conversation-log")
    state_path = args.state_file or os.path.join(log_dir, ".conversation-log-state.json")
    index_db = args.index_db or default_index_db()
    m_total, m_n = run_once(args.sessions_root, args.project_root, log_dir,
                            state_path, index_db, verbose)
    c_total, c_n = run_claude_once(args.project_root, log_dir, verbose)
    return m_total, m_n, c_total, c_n


def run_watch_all(args):
    log_dir = args.log_dir or os.path.join(args.project_root, "conversation-log")
    print(f"watching Muse + Claude Code sessions for {args.project_root} "
          f"(interval {args.interval}s, logs in {log_dir})", flush=True)
    while True:
        try:
            m_total, _, c_total, _ = run_all(args)
        except Exception as exc:  # keep the background logger alive
            print(f"warning: pass failed: {exc}", file=sys.stderr, flush=True)
        else:
            if m_total or c_total:
                stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{stamp}: appended {m_total} Muse + {c_total} Claude entries", flush=True)
        time.sleep(args.interval)


def agent_label(project_root):
    """One background logger per project: label carries the folder name and a
    short hash of its full path so two projects never collide."""
    name = re.sub(r"[^A-Za-z0-9]+", "-", os.path.basename(os.path.abspath(project_root))).strip("-")
    digest = hashlib.sha1(os.path.abspath(project_root).encode()).hexdigest()[:8]
    return f"com.agent-workflow.conversation-log.{name}.{digest}"


def _launchctl(*cmd):
    return subprocess.run(["launchctl", *cmd], capture_output=True, text=True)


def cmd_start(args):
    if sys.platform != "darwin":
        print("start is macOS-only. On this system run in a terminal:\n"
              f"  python3 {os.path.abspath(__file__)} watch")
        return 1
    label = agent_label(args.project_root)
    plist = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
    log_dir = os.path.join(args.project_root, "conversation-log")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(os.path.dirname(plist), exist_ok=True)
    watcher_log = os.path.join(log_dir, "watcher.log")
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{sys.executable}</string>
    <string>-I</string>
    <string>{os.path.abspath(__file__)}</string>
    <string>watch</string>
    <string>--project-root</string>
    <string>{os.path.abspath(args.project_root)}</string>
    <string>--interval</string>
    <string>{args.interval}</string>
  </array>
  <key>WorkingDirectory</key><string>{os.path.abspath(args.project_root)}</string>
  <key>StandardOutPath</key><string>{watcher_log}</string>
  <key>StandardErrorPath</key><string>{watcher_log}</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>15</integer>
</dict>
</plist>
"""
    with open(plist, "w", encoding="utf-8") as f:
        f.write(content)
    uid = os.getuid()
    _launchctl("bootout", f"gui/{uid}/{label}")  # replace any existing instance
    result = _launchctl("bootstrap", f"gui/{uid}", plist)
    if result.returncode != 0:
        print(f"could not start the background logger: {result.stderr.strip()}", file=sys.stderr)
        return 1
    print(f"Conversation logging started for {args.project_root}\n"
          f"  logs:   {log_dir}\n"
          f"  stop:   python3 tools/conversation-log.py stop\n"
          f"  status: python3 tools/conversation-log.py status")
    return 0


def cmd_stop(args):
    if sys.platform != "darwin":
        print("stop is macOS-only; on other systems just end the `watch` process (Ctrl+C).")
        return 1
    label = agent_label(args.project_root)
    plist = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
    result = _launchctl("bootout", f"gui/{os.getuid()}/{label}")
    existed = os.path.exists(plist)
    if existed:
        os.remove(plist)
    if result.returncode == 0 or existed:
        print(f"Conversation logging stopped for {args.project_root}. "
              "Existing logs are kept; run `start` to resume.")
    else:
        print("Conversation logging was not running for this project.")
    return 0


def cmd_status(args):
    if sys.platform != "darwin":
        print("status is macOS-only.")
        return 1
    label = agent_label(args.project_root)
    result = _launchctl("print", f"gui/{os.getuid()}/{label}")
    if result.returncode != 0:
        print("Conversation logging is NOT running for this project. "
              "Start it with: python3 tools/conversation-log.py start")
        return 0
    state = next((l.strip() for l in result.stdout.splitlines() if l.strip().startswith("state =")), "state = unknown")
    print(f"Conversation logging is running ({state}) for {args.project_root}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Log this project's Muse and Claude Code conversations to Markdown.")
    parser.add_argument("mode", nargs="?", default="once",
                        choices=["start", "stop", "status", "once", "watch"])
    parser.add_argument("--project-root", default=default_project_root())
    parser.add_argument("--sessions-root",
                        default=os.environ.get("MUSE_SESSIONS_ROOT") or default_sessions_root(),
                        help="Muse sessions directory")
    parser.add_argument("--log-dir", default=None)
    parser.add_argument("--state-file", default=None)
    parser.add_argument("--index-db", default=None)
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    args.project_root = os.path.abspath(args.project_root)

    if args.mode == "start":
        return cmd_start(args)
    if args.mode == "stop":
        return cmd_stop(args)
    if args.mode == "status":
        return cmd_status(args)
    if args.mode == "watch":
        run_watch_all(args)
        return 0
    m_total, m_n, c_total, c_n = run_all(args, args.verbose)
    print(f"Muse sessions: {m_n}, entries appended: {m_total} | "
          f"Claude sessions: {c_n}, entries appended: {c_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
