# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from datetime import datetime, timezone
import json
from pathlib import Path
import re

from ApplicationProtocol import file_bytes, require, sha256

PROGRESS = "re/automation/ApplicationWorkers/SolidWorksProgress.py"
JOURNAL = "readback/native-progress.jsonl"
LIMIT = 1024 * 1024


def progress_binding(owner):
    return {"source_revision": owner["source_revision"], "request_sha256": owner["request_sha256"],
            "process": {key: owner[key] for key in ("pid", "created", "session", "image")}}


def inspect_progress(content, binding, complete=False):
    require(isinstance(content, bytes) and 0 < len(content) <= LIMIT, "native progress byte limit exceeded")
    lines = content.splitlines(keepends=True)
    partial = not lines[-1].endswith(b"\n")
    require(not complete or not partial, "completed native progress has an incomplete event")
    if partial:
        lines = lines[:-1]
    require(0 < len(lines) <= 1024 and all(len(line) <= 16384 for line in lines), "native progress event limit exceeded")
    previous, pending, events = None, [], []
    for index, line in enumerate(lines, 1):
        try:
            event = json.loads(line)
        except RecursionError as error:
            raise ValueError("native progress event nesting exceeds its limit") from error
        require(isinstance(event, dict) and set(event) == {
            "sequence", "previous_sha256", "binding", "stage", "file", "status", "detail", "recorded_utc",
        }, "native progress event shape differs")
        require(type(event["sequence"]) is int and event["sequence"] == index
                and event["previous_sha256"] == previous and event["binding"] == binding,
                "native progress chain or owned request binding differs")
        stage, name, status = event["stage"], event["file"], event["status"]
        require(isinstance(stage, str) and re.fullmatch(r"[a-z][a-z_]{0,63}", stage)
                and (name is None or isinstance(name, str) and 0 < len(name) <= 256
                     and not any(character in name for character in "/\\:\x00"))
                and status in ("started", "completed", "failed")
                and (event["detail"] is None or isinstance(event["detail"], dict)),
                "native progress stage is invalid")
        require(isinstance(event["recorded_utc"], str) and len(event["recorded_utc"]) <= 64,
                "native progress time is invalid")
        timestamp = datetime.fromisoformat(event["recorded_utc"].replace("Z", "+00:00"))
        require(timestamp.tzinfo is not None and timestamp.utcoffset() == timezone.utc.utcoffset(timestamp),
                "native progress time must be UTC")
        if stage == "run":
            require(index == len(lines) and not pending and name is None
                    and status in ("completed", "failed")
                    and event["detail"] == {"outcome": "observed" if status == "completed" else "failed"},
                    "native progress run disposition is invalid")
        elif status == "started":
            pending.append((stage, name))
        else:
            require(pending and pending.pop() == (stage, name), "native progress stage completion differs")
        events.append(event)
        previous = sha256(line)
    require(not complete or events[-1]["stage"] == "run" and events[-1]["status"] == "completed",
            "native progress did not record complete observed execution")
    return {"sha256": sha256(content), "events": len(events), "last_event": events[-1],
            "pending_stages": [{"stage": stage, "file": name} for stage, name in pending],
            "incomplete_tail": partial}


def require_progress(report, owner, work=None):
    require(isinstance(report, dict) and set(report) == {"version", "journal_utf8", "sha256", "events", "write_error"}
            and report["version"] == 1 and report["write_error"] is None and isinstance(report["journal_utf8"], str),
            "native progress report is missing or incomplete")
    content = report["journal_utf8"].encode("utf-8")
    summary = inspect_progress(content, progress_binding(owner), complete=True)
    require(report["sha256"] == summary["sha256"] and type(report["events"]) is int
            and report["events"] == summary["events"], "native progress report digest or event count differs")
    if work is not None:
        require(file_bytes(Path(work) / JOURNAL, LIMIT) == content, "native progress differs from its retained journal")
    return {"native_progress_sha256": summary["sha256"], "native_progress_events": summary["events"]}


def recovery_progress(work, launch):
    if launch is None:
        return {"status": "unavailable", "reason": "no_direct_launch"}
    try:
        content = file_bytes(Path(work) / JOURNAL, LIMIT)
        return {"status": "retained", **inspect_progress(content, progress_binding(launch))}
    except FileNotFoundError:
        return {"status": "unavailable", "reason": "journal_not_published"}
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        return {"status": "invalid", "error_type": type(error).__name__}


# only the sole read-only final control may use the explicit no-save close path
def require_final_discard(report, control):
    state = control.get("close_state")
    operand = control.get("close_operand")
    require(isinstance(state, dict) and set(state) == {"save_flag", "read_only", "document_count"}
            and type(state["save_flag"]) is bool and state["read_only"] is True
            and type(state["document_count"]) is int and state["document_count"] == 1
            and isinstance(operand, str) and operand and control.get("close_method") == "quit_document"
            and control.get("document_visible_at_close") is False,
            "native progress lacks sole read-only final-control discard evidence")
    events = [json.loads(line) for line in report["journal_utf8"].splitlines()]
    hidden = [event for event in events if event["stage"] == "final_control_hidden"]
    require(len(hidden) == 2 and [event["status"] for event in hidden] == ["started", "completed"]
            and all(event["file"] == "control.SLDPRT" and event["detail"] == {"visible": False} for event in hidden),
            "native progress final-control visibility setting differs")
    closes = [event for event in events if event["stage"] == "quit_document"]
    require(len(closes) == 2 and [event["status"] for event in closes] == ["started", "completed"]
            and all(event["file"] == "control.SLDPRT" and event["detail"] == {"operand": operand} for event in closes),
            "native progress final-control discard stage or operand differs")
    start = events.index(closes[0])
    after = [index for index, event in enumerate(events)
             if event["stage"] == "control_after" and event["file"] == "control.SLDPRT"]
    require(len(after) == 2 and events[after[0]]["status"] == "started"
            and events[after[1]]["status"] == "completed"
            and events.index(hidden[1]) < after[0] < start < after[1]
            and any(after[0] < index < start and event["stage"] == "open_document"
                    and event["file"] == "control.SLDPRT" and event["status"] == "completed"
                    for index, event in enumerate(events)),
            "native progress final-control visibility setting did not precede its open and close")
    require(start > 0 and events[start - 1]["stage"] == "close_state"
            and events[start - 1]["status"] == "completed" and events[start - 1]["file"] == "control.SLDPRT"
            and events[start - 1]["detail"] == state,
            "native progress final-control discard state differs")
    require(start >= 3 and events[start - 3]["stage"] == "close_visibility"
            and events[start - 3]["status"] == "completed" and events[start - 3]["file"] == "control.SLDPRT"
            and events[start - 3]["detail"] == {"visible": False},
            "native progress final-control visibility getter differs")
