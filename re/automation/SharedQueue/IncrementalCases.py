# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path


# independent clients must observe bounded reconciliation through actual controller commands
class ProcessQueue:
    def __init__(self, root):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.store = root / "State"
        self.serial = 0
        self.command = [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "Controller.py"),
            "--store",
            str(self.store),
        ]
        self.run("init", "--max-running", "4")

    def run(self, *arguments, code=0):
        result = subprocess.run(
            [*self.command, *arguments],
            capture_output=True,
            encoding="utf-8",
            check=False,
            timeout=60,
        )
        if result.returncode != code:
            raise AssertionError(result.stdout + result.stderr)
        return json.loads(result.stdout) if code == 0 else result.stderr

    def record(self, value):
        self.serial += 1
        path = self.root / f"Record-{self.serial}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)

    def enqueue(self, request, jobs, revision=0, priority=50):
        return self.run(
            "enqueue",
            self.record(
                {
                    "queue_version": 1,
                    "request": request,
                    "revision": revision,
                    "priority": priority,
                    "jobs": jobs,
                }
            ),
        )


# semantic case values make independently queued work distinct despite opaque client aliases
def job(name, case, *, parents=(), inputs=None):
    return {
        "id": name,
        "kind": "fixture.incremental",
        "inputs": inputs or {},
        "depends_on": list(parents),
        "rule_version": "rule@1",
        "tool_version": "tool@1",
        "options": {"case": case},
    }


# quota accounting must match the durable relational state after every transition and rollback
def counters(queue):
    with closing(sqlite3.connect(queue.store / "ledger.sqlite3")) as database:
        values = dict(
            database.execute(
                "SELECT key,value FROM settings WHERE key IN ('shared_request_count','shared_subscription_count','shared_pending_count')"
            )
        )
        actual = {
            "shared_request_count": database.execute(
                "SELECT COUNT(*) FROM shared_requests"
            ).fetchone()[0],
            "shared_subscription_count": database.execute(
                "SELECT COUNT(*) FROM shared_members"
            ).fetchone()[0],
            "shared_pending_count": database.execute(
                "SELECT COUNT(*) FROM shared_jobs s JOIN jobs j ON j.id=s.job_id LEFT JOIN shared_cancelled c ON c.job_id=j.id WHERE c.job_id IS NULL AND j.state IN ('queued','running','waiting_evidence','waiting_application','waiting_ci')"
            ).fetchone()[0],
        }
        if values != actual:
            raise AssertionError(
                f"transactional counters drifted: {values} != {actual}"
            )
        return values


# a large independent backlog must not enter another request's reconciliation closure
def independent(queue):
    identities = []
    for index in range(96):
        result = queue.enqueue(f"request:{index:03d}", [job(f"local:{index}", index)])
        if (
            result["shared_reconciled_jobs"] != 1
            or result["shared_reconcile_passes"] != 1
        ):
            raise AssertionError("independent admission traversed unrelated queue work")
        identities.append(result["jobs"][f"local:{index}"])
    for index in range(12):
        result = queue.run("cancel-request", f"request:{index:03d}", "--revision", "1")
        if (
            result["shared_reconciled_jobs"] != 1
            or result["shared_reconcile_passes"] != 1
        ):
            raise AssertionError(
                "independent cancellation traversed unrelated queue work"
            )
    current = counters(queue)
    queue.run("queue-config", "--max-pending", str(current["shared_pending_count"]))
    before = counters(queue)
    queue.run(
        "enqueue",
        queue.record(
            {
                "queue_version": 1,
                "request": "overflow",
                "revision": 0,
                "jobs": [job("overflow", 999)],
            }
        ),
        code=1,
    )
    if counters(queue) != before:
        raise AssertionError("rejected admission changed quota counters")
    alias = queue.enqueue("alias", [job("renamed", 50)])
    if (
        alias["jobs"]["renamed"] != identities[50]
        or alias["shared_reconciled_jobs"] != 1
    ):
        raise AssertionError("shared alias did not reuse one existing work item")
    counters(queue)
    queue.run("queue-config", "--max-pending", "256")
    return identities


# standalone consumers must revive and release only the required shared ancestry
def dependency_changes(queue):
    parent = job("parent", 1000)
    left = job(
        "left", 1001, parents=("parent",), inputs={"source": {"dependency": "parent"}}
    )
    right = job(
        "right", 1002, parents=("parent",), inputs={"source": {"dependency": "parent"}}
    )
    leaf = job(
        "leaf",
        1003,
        parents=("left", "right"),
        inputs={"left": {"dependency": "left"}, "right": {"dependency": "right"}},
    )
    result = queue.enqueue("diamond", [parent, left, right, leaf])
    if result["shared_reconciled_jobs"] != 4:
        raise AssertionError("diamond admission did not use its exact ancestry")
    shared_leaf = result["jobs"]["leaf"]
    result = queue.run("cancel-request", "diamond", "--revision", "1")
    if result["shared_reconciled_jobs"] != 4 or result["cancelled_jobs"] != 4:
        raise AssertionError("diamond cancellation missed its shared closure")
    before = counters(queue)["shared_pending_count"]
    consumer = job(
        "standalone:consumer",
        1004,
        parents=(shared_leaf,),
        inputs={"source": {"dependency": shared_leaf}},
    )
    queue.run("submit", queue.record(consumer))
    if counters(queue)["shared_pending_count"] != before + 4:
        raise AssertionError("standalone consumer did not restore its shared ancestors")
    queue.run("submit", queue.record(job("standalone:consumer", 1005)))
    if counters(queue)["shared_pending_count"] != before:
        raise AssertionError("removed standalone dependency retained orphan ancestry")
    events = queue.run("events")["events"]
    latest = next(
        json.loads(row["detail"])
        for row in events
        if row["action"] == "shared_members_reconciled"
    )
    if latest["examined_jobs"] != 4:
        raise AssertionError("standalone update scanned unrelated shared roots")


# pending counters must follow actual completion invalidation cancellation and resubscription
def input_changes(queue):
    evidence = queue.root / "Evidence.bin"
    evidence.write_bytes(b"first observation")
    queue.run("bind", "evidence:incremental", str(evidence))
    spec = job("input:case", 2000, inputs={"source": "evidence:incremental"})
    result = queue.enqueue("input:request", [spec], priority=100)
    identity = result["jobs"]["input:case"]
    baseline = counters(queue)["shared_pending_count"]
    lease = queue.root / "Lease.json"
    claim = queue.run(
        "claim", "--worker", "fixture:incremental", "--claim-file", str(lease)
    )
    if claim["job"] != identity:
        raise AssertionError(
            "priority input case did not acquire the real worker claim"
        )
    queue.run(
        "finish",
        "--lease",
        str(lease),
        "--result",
        queue.record({"observed": True}),
        "--outcome",
        "completed",
        "--reason",
        "fixture completed",
    )
    if counters(queue)["shared_pending_count"] != baseline - 1:
        raise AssertionError("completion did not release one pending counter")
    evidence.write_bytes(b"second observation")
    queue.run("bind", "evidence:incremental", str(evidence))
    if counters(queue)["shared_pending_count"] != baseline:
        raise AssertionError("input invalidation did not restore pending accounting")
    queue.run("cancel-request", "input:request", "--revision", "1")
    if counters(queue)["shared_pending_count"] != baseline - 1:
        raise AssertionError("cancellation did not retire pending accounting")
    evidence.write_bytes(b"third observation")
    queue.run("bind", "evidence:incremental", str(evidence))
    if counters(queue)["shared_pending_count"] != baseline - 1:
        raise AssertionError("cancelled input work resurrected its pending counter")
    result = queue.enqueue("input:request", [spec], revision=2, priority=100)
    if (
        counters(queue)["shared_pending_count"] != baseline
        or result["shared_reconciled_jobs"] != 1
    ):
        raise AssertionError("resubscription did not restore exactly the required work")


# old extension stores need one transactional counter migration without changing their jobs
def migration(root):
    queue = ProcessQueue(root)
    queue.enqueue("legacy:first", [job("legacy:job", 3000)])
    with closing(sqlite3.connect(queue.store / "ledger.sqlite3")) as database:
        for name in (
            "shared_request_added",
            "shared_request_removed",
            "shared_member_added",
            "shared_member_removed",
            "shared_pending_added",
            "shared_pending_removed",
            "shared_pending_cancelled",
            "shared_pending_restored",
            "shared_pending_state",
        ):
            database.execute(f"DROP TRIGGER {name}")
        database.execute(
            "DELETE FROM settings WHERE key IN ('shared_queue_counters_version','shared_request_count','shared_subscription_count','shared_pending_count')"
        )
        database.commit()
    result = queue.enqueue("legacy:second", [job("legacy:other", 3001)])
    values = counters(queue)
    if (
        values["shared_request_count"] != 2
        or values["shared_pending_count"] != 2
        or result["shared_reconciled_jobs"] != 1
    ):
        raise AssertionError("old shared extension did not migrate its counter state")


# process results bind the scaling claim to observed reconciliation scopes rather than wall clock guesses
def main():
    with tempfile.TemporaryDirectory(prefix="kit-incremental-queue-") as temporary:
        root = Path(temporary)
        queue = ProcessQueue(root / "Current")
        independent(queue)
        dependency_changes(queue)
        input_changes(queue)
        migration(root / "Legacy")
        totals = counters(queue)
    print(
        json.dumps(
            {
                "status": "passed",
                "scenario": "incremental",
                "independent_requests": 96,
                "maximum_independent_closure": 1,
                "diamond_closure": 4,
                "counters_verified": True,
                "legacy_migration_verified": True,
                "final_pending_jobs": totals["shared_pending_count"],
            }
        )
    )


if __name__ == "__main__":
    main()
