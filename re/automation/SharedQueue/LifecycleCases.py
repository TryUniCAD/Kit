# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from ProcessClient import Client, job


def check_supersession(root):
    client = Client(root / "Supersession")
    installation = "application:fixture"
    client.run("resource", installation, "--capacity", "1", "--available")
    first = client.enqueue("owner:first", [job("local:first", resources=[installation])])
    second = client.enqueue("owner:second", [job("local:second", resources=[installation])])
    old = first["jobs"]["local:first"]
    assert second["jobs"]["local:second"] == old
    claimed, lease = client.claim("Original")
    assert claimed == old
    client.run("cancel-request", "owner:first", "--revision", "1")
    client.run("heartbeat", "--lease", lease)
    assert client.state(old)["state"] == "running"
    assert client.run("queue-status", "--request", "owner:first")["requests"][0]["active"] is False
    replacement = client.enqueue(
        "owner:second",
        [job("local:second", resources=[installation], tool_version="tool@2")],
        revision=1,
    )["jobs"]["local:second"]
    assert replacement != old
    client.run("heartbeat", "--lease", lease, code=3)
    client.finish(lease, code=3)
    assert client.state(old)["state"] == "rejected"
    assert client.state(old)["reason"] == "shared request superseded"
    assert client.run("resource", installation, "--capacity", "1")["available"] is False
    assert client.claim("UnsafeRestart")[0] is None
    client.run("resource", installation, "--available")
    claimed, replacement_lease = client.claim("Replacement")
    assert claimed == replacement
    client.finish(replacement_lease)
    client.run("cancel-request", "owner:first", "--revision", "1")
    client.run("cancel-request", "owner:second", "--revision", "0", code=1)
    return {"subscriber_preserved": True, "stale_finish_refused": True, "resource_quarantined": True}


def check_invalidation(root):
    client = Client(root / "Invalidation")
    evidence = client.root / "Evidence.bin"
    evidence.write_bytes(b"first evidence")
    client.run("bind", "evidence:fixture", evidence)
    spec = job("local:decode", inputs={"source": "evidence:fixture"})
    shared = client.enqueue("reader:current", [spec])["jobs"]["local:decode"]
    claimed, first_lease = client.claim("FirstInput")
    assert claimed == shared
    client.finish(first_lease)
    completed = client.state(shared)
    receipt = completed["receipt"]
    client.run("cancel-request", "reader:current", "--revision", "1")
    assert client.state(shared)["state"] == "completed"
    evidence.write_bytes(b"changed evidence")
    client.run("bind", "evidence:fixture", evidence)
    assert client.state(shared)["state"] == "rejected"
    assert client.claim("OrphanInput")[0] is None
    client.run("artifact", receipt)
    resubmitted = client.enqueue("reader:current", [spec], revision=2)
    assert resubmitted["jobs"]["local:decode"] == shared
    assert resubmitted["reused_jobs"] == 0
    claimed, second_lease = client.claim("NewInput")
    assert claimed == shared
    client.run("heartbeat", "--lease", first_lease, code=3)
    client.finish(second_lease)
    current = client.state(shared)
    assert current["fingerprint"] != completed["fingerprint"]
    assert current["generation"] > completed["generation"]
    assert current["result"] == completed["result"]
    client.run("artifact", receipt)
    return {"orphan_not_resurrected": True, "changed_input_replayed": True, "historical_receipt_retained": True}


def check_dependents(root):
    client = Client(root / "Dependents")
    parent = client.enqueue("parent:owner", [job("local:parent")])["jobs"]["local:parent"]
    standalone = client.write(
        job("standalone:child", depends_on=[parent], inputs={"parent": {"dependency": parent}})
    )
    client.run("submit", standalone)
    client.run("cancel-request", "parent:owner", "--revision", "1")
    assert client.state(parent)["state"] == "queued"
    claimed, lease = client.claim("RetainedParent")
    assert claimed == parent
    client.finish(lease)
    claimed, lease = client.claim("StandaloneChild")
    assert claimed == "standalone:child"
    client.finish(lease)
    return {"standalone_dependency_preserved": True}
