# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from CodexAdvice.SharedBudget import SharedBudget
from CodexAdvice.SharedSmoke import command, settle, setup, start


# deterministic identities let long churn campaigns prove admission beyond the old metadata ceiling
def identity(value):
    return hashlib.sha256(value.encode()).hexdigest()


# a separate producer exercises durable admission while another request retains the native provider slot
def producer(args):
    budget = SharedBudget(args.directory / "Shared", "codex", 10000, 1)
    calls = [0]

    # vm work gives a deterministic polling bound independent of machine load and disk latency
    def progress():
        calls[0] += 100
        return 0

    if args.operation == "poll":
        budget.db.set_progress_handler(progress, 100)
    try:
        for index in range(args.count):
            key = identity(args.operation + ":" + str(index))
            token = identity("waiter:" + str(index))
            result = budget.reserve(key, token, 1)
            assert result["status"] == "waiting", result
            budget.leave(token)
        budget.db.set_progress_handler(None, 0)
        count = budget.request_count()
    finally:
        budget.close()
    print(json.dumps({"requests": args.count, "vm_steps": calls[0], "retained": count}))


# all terminal evidence originates in a real disposable provider call before historical fixtures are expanded
def prepare(parent, name):
    root = setup(parent, name)
    settle(start(root, "Complete", "completed context", limit=10000))
    settle(start(root, "Uncertain", "uncertain context", limit=10000, ADVICE_FAIL="1"))
    snapshot = command(root, "status")
    assert snapshot["providers"][0]["used"] == 2
    assert snapshot["reservations"][0]["state"] == "uncertain"
    return root


# public metadata remains verifiable against the actual database after successful or rolled back intake
def totals(root):
    with sqlite3.connect(root / "Shared/Advice.sqlite3") as db:
        counter = db.execute(
            "SELECT value FROM advice_metadata WHERE key='request_count'"
        ).fetchone()[0]
        actual, charged = db.execute(
            "SELECT COUNT(*),SUM(charged) FROM requests"
        ).fetchone()
        used = db.execute("SELECT used FROM providers WHERE name='codex'").fetchone()[0]
    assert counter == actual
    return counter, charged, used


# polling must not traverse paid history or release another providers charged work
def polling(parent):
    small = prepare(parent, "Small")
    large = prepare(parent, "Large")
    with sqlite3.connect(large / "Shared/Advice.sqlite3") as db:
        proposal = db.execute(
            "SELECT proposal FROM requests WHERE state='done'"
        ).fetchone()[0]
        db.executemany(
            "INSERT INTO requests(provider,request_key,state,created,proposal,charged) VALUES ('codex',?,'done',?,?,1)",
            [
                (identity("history:" + str(index)), index, proposal)
                for index in range(7998)
            ],
        )
        db.execute("UPDATE providers SET used=8000 WHERE name='codex'")
        db.execute("INSERT INTO providers VALUES ('claude',10000,1,1)")
        db.execute(
            "INSERT INTO requests(provider,request_key,state,created,deadline,charged) VALUES ('claude',?,'running',0,0,1)",
            (identity("other-running"),),
        )
        db.execute(
            "INSERT INTO requests(provider,request_key,state,created,charged) VALUES ('claude',?,'queued',0,0)",
            (identity("other-queued"),),
        )
        db.execute(
            "INSERT INTO waiters VALUES ('claude',?,?,0)",
            (identity("other-queued"), identity("other-waiter")),
        )
        db.execute(
            "UPDATE advice_metadata SET value=(SELECT COUNT(*) FROM requests) WHERE key='request_count'"
        )
    reports = []
    for root in (small, large):
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--directory",
                str(root),
                "--operation",
                "poll",
                "--count",
                "40",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        reports.append(json.loads(result.stdout))
    assert reports[1]["vm_steps"] <= reports[0]["vm_steps"] * 2 + 2000, reports
    assert totals(large) == (8001, 8001, 8000)
    with sqlite3.connect(large / "Shared/Advice.sqlite3") as db:
        assert (
            db.execute(
                "SELECT state FROM requests WHERE provider='claude' AND request_key=?",
                (identity("other-running"),),
            ).fetchone()[0]
            == "running"
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM waiters WHERE provider='claude'"
            ).fetchone()[0]
            == 0
        )
    return reports


# dead callers from another provider must yield capacity beyond each bounded polling cleanup batch
def cap_expiry(parent):
    root = prepare(parent, "ForeignCapacity")
    with sqlite3.connect(root / "Shared/Advice.sqlite3") as db:
        proposal = db.execute(
            "SELECT proposal FROM requests WHERE state='done'"
        ).fetchone()[0]
        paid = [identity("paid:" + str(index)) for index in range(998)]
        queued = [identity("foreign:" + str(index)) for index in range(9000)]
        db.executemany(
            "INSERT INTO requests(provider,request_key,state,created,proposal,charged) VALUES ('codex',?,'done',0,?,1)",
            [(key, proposal) for key in paid],
        )
        db.execute("UPDATE providers SET used=1000 WHERE name='codex'")
        db.execute("INSERT INTO providers VALUES ('claude',10000,1,0)")
        db.executemany(
            "INSERT INTO requests(provider,request_key,state,created,charged) VALUES ('claude',?,'queued',0,0)",
            [(key,) for key in queued],
        )
        db.executemany(
            "INSERT INTO waiters VALUES ('codex',?,?,0)",
            [(key, identity("paid-waiter:" + key)) for key in paid[:256]],
        )
        db.executemany(
            "INSERT INTO waiters VALUES ('claude',?,?,1)",
            [(key, identity("foreign-waiter:" + key)) for key in queued],
        )
        db.execute("UPDATE advice_metadata SET value=10000 WHERE key='request_count'")
    settle(start(root, "Reclaim", "new intake", limit=10000, seconds=1))
    report = json.loads((root / "Reclaim.json").read_text())
    assert report["attempts"][-1]["status"] == "shared_wait_timeout"
    count, charged, used = totals(root)
    assert 1000 <= count < 10000 and charged == used == 1000
    assert command(root, "status")["reservations"][0]["state"] == "uncertain"


# abandoned prompts beyond the historical cap must not exhaust slots or erase any charged outcome
def churn(parent):
    root = prepare(parent, "Churn")
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--directory",
            str(root),
            "--operation",
            "churn",
            "--count",
            "10020",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=150,
    )
    report = json.loads(result.stdout)
    assert report["requests"] == 10020 and report["retained"] == 2
    assert totals(root) == (2, 2, 2)
    snapshot = command(root, "status")
    assert snapshot["reservations"][0]["state"] == "uncertain"
    cap_expiry(parent)
    report["foreign_capacity_reclaimed"] = True
    return report


# saved version one stores include orphan rows and live callers that migration must distinguish
def legacy(parent):
    root = setup(parent, "Migration")
    shared = root / "Shared"
    shared.mkdir(mode=0o700)
    database = shared / "Advice.sqlite3"
    with sqlite3.connect(database) as db:
        db.executescript("""
        CREATE TABLE providers (name TEXT PRIMARY KEY, call_limit INTEGER NOT NULL, parallel INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE requests (provider TEXT NOT NULL, request_key TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('queued','running','uncertain','done','failed','abandoned')), created REAL NOT NULL, deadline REAL, owner TEXT, proposal TEXT, attempts TEXT, PRIMARY KEY(provider,request_key));
        CREATE INDEX request_queue ON requests(provider,state,created,request_key);
        CREATE TABLE waiters (provider TEXT NOT NULL,request_key TEXT NOT NULL,token TEXT NOT NULL PRIMARY KEY,until_at REAL NOT NULL);
        CREATE INDEX request_waiters ON waiters(provider,request_key,until_at);
        INSERT INTO providers VALUES ('codex',10000,1,4);
        PRAGMA user_version=1;
        """)
        rows = [
            ("done", "done"),
            ("failed", "failed"),
            ("uncertain", "uncertain"),
            ("running", "running"),
            ("abandoned", "abandoned"),
            ("orphan", "queued"),
            ("live", "queued"),
            ("expired", "queued"),
        ]
        db.executemany(
            "INSERT INTO requests(provider,request_key,state,created,deadline) VALUES ('codex',?,?,0,0)",
            [(identity(name), state) for name, state in rows],
        )
        db.execute(
            "INSERT INTO waiters VALUES ('codex',?,?,?)",
            (identity("live"), identity("live-token"), time.time() + 120),
        )
        db.execute(
            "INSERT INTO waiters VALUES ('codex',?,?,0)",
            (identity("expired"), identity("expired-token")),
        )
    database.chmod(0o600)
    failed = start(root, "BadMigration", limit=9999)
    stdout, stderr = failed.communicate(timeout=10)
    assert failed.returncode == 1 and "limits differ" in stderr, (stdout, stderr)
    with sqlite3.connect(database) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        assert (
            db.execute(
                "SELECT 1 FROM sqlite_master WHERE name='advice_metadata'"
            ).fetchone()
            is None
        )
        assert db.execute("SELECT COUNT(*) FROM requests").fetchone()[0] == 8
    snapshot = command(root, "status")
    assert snapshot["providers"][0]["used"] == 4
    assert totals(root) == (5, 4, 4)
    with sqlite3.connect(database) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
        assert (
            db.execute(
                "SELECT charged FROM requests WHERE request_key=?", (identity("live"),)
            ).fetchone()[0]
            == 0
        )
        db.execute(
            "CREATE TRIGGER reject_waiters BEFORE INSERT ON waiters BEGIN SELECT RAISE(ABORT,'fixture intake failed'); END"
        )
    failed = start(root, "Rollback", "rollback context", limit=10000)
    stdout, stderr = failed.communicate(timeout=10)
    assert failed.returncode == 1 and "fixture intake failed" in stderr, (
        stdout,
        stderr,
    )
    assert totals(root) == (5, 4, 4)
    with sqlite3.connect(database) as db:
        db.execute("DROP TRIGGER reject_waiters")
    return {"migration_version": 2, "rolled_back": True, "charged_history": 4}


# the normal shared suite drives all metadata scenarios through independent processes and durable stores
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--operation", choices=("poll", "churn"))
    parser.add_argument("--count", type=int, default=40)
    args = parser.parse_args()
    if args.operation:
        producer(args)
        return
    if os.name != "posix":
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("FailureSmoke.py")),
                "--directory",
                str(args.directory),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        assert '"failure_fencing": true' in result.stdout
        print(
            json.dumps(
                {
                    "metadata_checks": 3,
                    "live_provider_calls": 0,
                    "shared_advice_supported": False,
                }
            )
        )
        return
    reports = {
        "polling": polling(args.directory),
        "churn": churn(args.directory),
        "migration": legacy(args.directory),
    }
    print(
        json.dumps({"metadata_checks": 3, "live_provider_calls": 0, "reports": reports})
    )


if __name__ == "__main__":
    main()
