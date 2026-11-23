# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from CodexAdvice.MetadataSmoke import identity, prepare, totals
from CodexAdvice.SharedBudget import SharedBudget
from CodexAdvice.SharedSmoke import events, settle, setup, start


# process barriers keep metadata writes outside the measured idle interval
def wait_for(path):
    deadline = time.monotonic() + 40
    while not path.exists():
        if time.monotonic() >= deadline:
            raise AssertionError("process barrier timed out " + str(path))
        time.sleep(0.02)


# many independent callers must join once and observe busy capacity without durable writes
def producer(args):
    root = args.directory
    budget = SharedBudget(root / "Shared", "codex", 10000, 1)
    statements = {"writers": 0, "mutations": 0}

    # sqlite traces distinguish transactional acquisition from ordinary read snapshots
    def trace(statement):
        text = statement.strip().upper()
        if text.startswith("BEGIN IMMEDIATE"):
            statements["writers"] += 1
        if text.startswith(("INSERT", "UPDATE", "DELETE")):
            statements["mutations"] += 1

    budget.db.set_trace_callback(trace)
    members = [
        (
            identity("request:" + str(args.worker) + ":" + str(index)),
            identity("token:" + str(args.worker) + ":" + str(index)),
        )
        for index in range(250)
    ]
    lease = time.time() + 180
    for key, token in members:
        assert budget.reserve(key, token, 180, wait_until=lease)["status"] == "waiting"
    joined = dict(statements)
    (root / ("Ready" + str(args.worker))).touch()
    wait_for(root / "StartPolling")
    statements["writers"] = statements["mutations"] = 0
    changes = budget.db.total_changes
    version = budget.db.execute("PRAGMA data_version").fetchone()[0]
    for _ in range(4):
        for key, token in members:
            assert (
                budget.reserve(key, token, 180, wait_until=lease)["status"] == "waiting"
            )
    idle = dict(statements)
    assert idle == {"writers": 0, "mutations": 0}, idle
    assert changes == budget.db.total_changes
    assert version == budget.db.execute("PRAGMA data_version").fetchone()[0]
    (root / ("Idle" + str(args.worker) + ".json")).write_text(
        json.dumps({"joined": joined, "idle": idle, "polls": 1000})
    )
    wait_for(root / "AllowLeave")
    for _, token in members:
        budget.leave(token)
    budget.close()


# four producer processes reproduce a thousand shared waiters without a live provider account
def many_waiters(parent):
    root = prepare(parent, "ManyWaiters")
    children = [
        subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--directory",
                str(root),
                "--operation",
                "producer",
                "--worker",
                str(index),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for index in range(4)
    ]
    try:
        for index in range(4):
            wait_for(root / ("Ready" + str(index)))
        assert totals(root) == (1002, 2, 2)
        (root / "StartPolling").touch()
        reports = []
        for index in range(4):
            path = root / ("Idle" + str(index) + ".json")
            wait_for(path)
            reports.append(json.loads(path.read_text()))
        assert sum(report["joined"]["writers"] for report in reports) == 1000
        assert sum(report["idle"]["writers"] for report in reports) == 0
        assert sum(report["idle"]["mutations"] for report in reports) == 0
        (root / "AllowLeave").touch()
        for process in children:
            settle(process)
    finally:
        for process in children:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
    assert totals(root) == (2, 2, 2)
    assert len([row for row in events(root) if row["event"] == "start"]) == 2
    return {
        "waiters": 1000,
        "idle_polls": 4000,
        "idle_writer_transactions": 0,
        "idle_mutations": 0,
    }


# an expired caller must never restart its lease or become eligible through repeated observation
def expired(parent):
    root = prepare(parent, "ExpiredWaiter")
    budget = SharedBudget(root / "Shared", "codex", 10000, 1)
    key, token = identity("expired-request"), identity("expired-token")
    assert budget.reserve(key, token, 1)["status"] == "waiting"
    until = budget.db.execute(
        "SELECT until_at FROM waiters WHERE token=?", (token,)
    ).fetchone()[0]
    before = budget.db.total_changes
    time.sleep(1.1)
    assert budget.reserve(key, token, 1)["status"] == "wait_expired"
    assert budget.db.total_changes == before
    assert (
        budget.db.execute(
            "SELECT until_at FROM waiters WHERE token=?", (token,)
        ).fetchone()[0]
        == until
    )
    budget.leave(token)
    budget.close()
    assert totals(root) == (2, 2, 2)


# a waiting writer must recheck the callers deadline after acquiring the sqlite lock
def lock_holder(args):
    with sqlite3.connect(
        args.directory / "Shared/Advice.sqlite3", isolation_level=None
    ) as db:
        db.execute("BEGIN IMMEDIATE")
        (args.directory / "Locked").touch()
        time.sleep(1.6)
        db.execute("ROLLBACK")


# stale admission observations cannot spend a call after a delayed writer transaction begins
def contention(parent):
    root = setup(parent, "WriterContention")
    budget = SharedBudget(root / "Shared", "codex", 10000, 1)
    budget.close()
    locker = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--directory",
            str(root),
            "--operation",
            "lock",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        wait_for(root / "Locked")
        settle(start(root, "Late", "delayed admission", limit=10000, seconds=1))
        settle(locker)
    finally:
        if locker.poll() is None:
            locker.kill()
            locker.communicate(timeout=5)
    report = json.loads((root / "Late.json").read_text())
    assert (
        report["proposal"] is None
        and report["attempts"][-1]["status"] == "shared_wait_expired"
    ), report
    assert totals(root) == (0, None, 0)
    assert events(root) == []


# the complete suite exercises idle polling and reservation races through real processes and sqlite
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--operation", choices=("producer", "lock"))
    parser.add_argument("--worker", type=int, default=0)
    args = parser.parse_args()
    if args.operation == "producer":
        producer(args)
        return
    if args.operation == "lock":
        lock_holder(args)
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
                    "read_only_polling": True,
                    "live_provider_calls": 0,
                    "shared_advice_supported": False,
                }
            )
        )
        return
    report = many_waiters(args.directory)
    expired(args.directory)
    contention(args.directory)
    print(
        json.dumps(
            {"read_only_polling": True, "live_provider_calls": 0, "report": report}
        )
    )


if __name__ == "__main__":
    main()
