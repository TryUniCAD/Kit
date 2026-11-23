# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json

from ProcessClient import Client, job, race


def check_races(root):
    client = Client(root / "Races")
    paths = [
        client.write(
            {
                "queue_version": 1,
                "request": f"client:{index}",
                "revision": 0,
                "jobs": [job(f"local:{index}")],
            }
        )
        for index in range(6)
    ]
    enqueued = race(client.command, [("enqueue", path) for path in paths])
    identities = {next(iter(item["jobs"].values())) for item in enqueued}
    assert len(identities) == 1, enqueued
    identity = identities.pop()
    assert identity.startswith("shared:")
    assert len(client.run("status")["jobs"]) == 1
    assert client.run("queue-status")["subscriptions"] == 6
    claims = race(
        client.command,
        [
            (
                "claim",
                "--worker",
                f"worker:{index}",
                "--claim-file",
                client.root / f"RaceLease-{index}.json",
            )
            for index in range(6)
        ],
    )
    winners = [index for index, item in enumerate(claims) if item["job"]]
    assert len(winners) == 1, claims
    assert claims[winners[0]]["job"] == identity
    client.finish(client.root / f"RaceLease-{winners[0]}.json")
    assert client.state(identity)["attempts"] == 1
    cached = client.enqueue("cache:reader", [job("cache:local")])
    assert cached["jobs"]["cache:local"] == identity
    assert cached["reused_jobs"] == 1
    assert client.claim("AfterCache")[0] is None
    repeated = client.run("enqueue", paths[0])
    assert repeated["idempotent"] is True
    client.enqueue("client:0", [job("local:0", tool_version="tool@2")], code=1)
    client.enqueue("client:0", [job("local:0")], revision=1)
    client.run("enqueue", paths[0], code=1)
    assert client.state(identity)["state"] == "completed"
    forged = client.write(job(identity, tool_version="foreign@2"))
    client.run("submit", forged, code=1)
    assert client.state(identity)["attempts"] == 1
    return {"concurrent_subscribers": 6, "issued_claims": 1, "cache_reused": True}


def check_graph(root):
    client = Client(root / "Graph")
    first = client.enqueue(
        "graph:first",
        [
            job("first:child", depends_on=["first:parent"], inputs={"parent": {"dependency": "first:parent"}}),
            job("first:parent", options={"role": "parent"}),
        ],
    )
    second = client.enqueue(
        "graph:second",
        [
            job("second:parent", options={"role": "parent"}),
            job("second:child", depends_on=["second:parent"], inputs={"parent": {"dependency": "second:parent"}}),
        ],
    )
    parent = first["jobs"]["first:parent"]
    child = first["jobs"]["first:child"]
    assert second["jobs"]["second:parent"] == parent
    assert second["jobs"]["second:child"] == child
    assert second["shared_jobs"] == 2
    assert client.state(child)["state"] == "waiting_evidence"
    claimed, lease = client.claim("Parent")
    assert claimed == parent
    assert client.claim("BlockedChild")[0] is None
    client.finish(lease)
    claimed, lease = client.claim("Child")
    assert claimed == child
    manifest = json.loads(lease.read_text(encoding="utf-8"))
    assert manifest["job"]["depends_on"] == [parent]
    assert manifest["job"]["inputs"]["parent"]["dependency"] == parent
    assert manifest["snapshot"]["inputs"]["parent"]["sha256"] == client.state(parent)["result"]
    client.finish(lease)
    assert len(client.run("status")["jobs"]) == 2
    client.enqueue(
        "graph:cycle",
        [job("cycle:first", depends_on=["cycle:second"]), job("cycle:second", depends_on=["cycle:first"])],
        code=1,
    )
    assert len(client.run("status")["jobs"]) == 2
    return {"shared_dependency_graph": 2, "selectors_remapped": True, "cycle_rollback": True}
