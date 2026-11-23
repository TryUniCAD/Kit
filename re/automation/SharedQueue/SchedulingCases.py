# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sqlite3
import time

from ProcessClient import Client, job


def check_limits(root):
    client = Client(root / "Limits")
    client.run("queue-config", "--max-pending", "1")
    first = client.enqueue("limit:first", [job("local:first")])["jobs"]["local:first"]
    client.enqueue("limit:second", [job("local:alias")])
    before = client.run("queue-status")
    client.enqueue("limit:overflow", [job("local:other", options={"case": "other"})], code=1)
    after = client.run("queue-status")
    assert before["requests"] == after["requests"]
    assert before["pending_jobs"] == after["pending_jobs"] == 1
    assert len(client.run("status")["jobs"]) == 1
    client.enqueue("limit:first", [job("local:replacement", options={"case": "replacement"})], revision=1, code=1)
    assert client.run("queue-status", "--request", "limit:first")["requests"][0]["revision"] == 0
    claimed, lease = client.claim("BeforeLimit")
    assert claimed == first
    client.finish(lease)
    client.enqueue("limit:overflow", [job("local:other", options={"case": "other"})])
    assert client.run("queue-status")["pending_jobs"] == 1
    client.run("queue-config", "--max-pending", "0", code=1)
    client.run("queue-config", "--max-pending", "10001", code=1)
    malformed = client.write({"queue_version": True, "request": "invalid", "revision": 0, "jobs": [job("bad")]})
    client.run("enqueue", malformed, code=1)
    return {"pending_limit_atomic": True, "duplicate_admitted_at_limit": True}


def check_priority(root):
    client = Client(root / "Priority")
    low = client.enqueue("rank:low", [job("local:low", options={"case": "low"})], priority=0)["jobs"]["local:low"]
    high = client.enqueue("rank:high", [job("local:high", options={"case": "high"})], priority=100)["jobs"]["local:high"]
    claimed, lease = client.claim("HighPriority")
    assert claimed == high
    client.finish(lease)
    assert client.state(low)["state"] == "queued"
    newer = client.enqueue("rank:new", [job("local:new", options={"case": "new"})], priority=100)["jobs"]["local:new"]
    with sqlite3.connect(client.root / "State/ledger.sqlite3", timeout=30) as database:
        database.execute("UPDATE jobs SET created=? WHERE id=?", (time.time() - 121 * 60, low))
    claimed, lease = client.claim("AgedPriority")
    assert claimed == low
    client.finish(lease)
    assert client.claim("NewPriority")[0] == newer
    return {"priority_respected": True, "aging_prevents_starvation": True}


def check_resources(root):
    client = Client(root / "Resources")
    installation = "application:fixture"
    client.run("resource", installation, "--capacity", "1", "--available")
    client.run("pool", "native", "--kind", "fixture.native")
    client.run("pool", "decode", "--kind", "fixture.decode")
    native = client.enqueue(
        "native:owner",
        [job("native:first", kind="fixture.native", resources=[installation], options={"case": "first"}), job("native:second", kind="fixture.native", resources=[installation], options={"case": "second"})],
    )["jobs"]
    offline = client.enqueue("offline:owner", [job("offline:first")])["jobs"]["offline:first"]
    claimed, native_lease = client.claim("NativeFirst", "native")
    assert claimed in native.values()
    assert client.claim("NativeBusy", "native")[0] is None
    claimed, offline_lease = client.claim("OfflineReady", "decode")
    assert claimed == offline
    client.finish(offline_lease)
    client.finish(native_lease)
    assert client.claim("NativeNext", "native")[0] in native.values()
    return {"exclusive_installation": True, "offline_progress_during_native_work": True}


def check_grouped(root):
    client = Client(root / "Grouped")
    source = client.root / "Input.bin"
    source.write_bytes(b"small shared input")
    client.run("bind", "evidence:group", source)
    client.run("pool", "decode", "--kind", "fixture.decode")
    jobs = [job(f"local:{index}", inputs={"source": "evidence:group"}, options={"case": index}) for index in range(2)]
    mappings = client.enqueue("group:owner", jobs)["jobs"]
    registry = client.write({"group_registry_version": 1, "kinds": {"fixture.decode": {"limit_bytes": 1048576, "max_members": 4}}})
    directory = client.root / "Group"
    result = client.run("claim-group", "--worker", "worker:group", "--pool", "decode", "--registry", registry, "--claim-dir", directory)
    assert result["count"] == 2
    for identity in mappings.values():
        assert client.state(identity)["state"] == "running"
    client.run("cancel-request", "group:owner", "--revision", "1")
    result = client.run("heartbeat-group", "--lease", directory)
    assert result["stale"] is True
    assert all(member["stale"] for member in result["members"])
    assert all(client.state(identity)["state"] == "rejected" for identity in mappings.values())
    assert client.claim("AfterGroup")[0] is None
    return {"grouped_claims_fenced": 2}
