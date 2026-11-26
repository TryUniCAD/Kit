# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ProcessClient import Client, job


def check_supervisor(root):
    client = Client(root / "Supervisor")
    automation = Path(__file__).resolve().parents[1]
    schema_process = subprocess.run(
        [sys.executable, str(automation / "InferenceRunner.py"), "--schema"],
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    assert schema_process.returncode == 0, schema_process.stderr
    inference_schema = client.write(json.loads(schema_process.stdout))
    fixture_schema = client.write({"type": "object"})
    marker = client.root / "OwnedWorker.json"
    gap = client.write(
        {
            "inference_version": 1,
            "scope": "shared-queue-fixture",
            "status": "corroborated",
            "affected_archives": {
                hashlib.sha256(b"synthetic fusion identity").hexdigest(): "fusion.f3d",
                hashlib.sha256(b"synthetic solidworks identity").hexdigest(): "solidworks.sldprt",
            },
            "corroboration": {"fixture": "independently authored protocol observation"},
        }
    )
    client.run("bind", "evidence:gap", gap)
    work = client.enqueue(
        "supervised:inference",
        [job("local:inference", kind="inference.paired-gap", inputs={"plan": "evidence:gap"}, options={"scope": "shared-queue-fixture"}, lease_seconds=3, timeout_seconds=60)],
    )["jobs"]["local:inference"]
    owned = client.enqueue(
        "supervised:owned",
        [job("local:owned", kind="fixture.owned", options={"marker": str(marker)}, lease_seconds=3, timeout_seconds=60)],
    )["jobs"]["local:owned"]
    registry = client.write(
        {
            "runners": {
                "inference.paired-gap": {
                    "pool": "inference",
                    "argv": [sys.executable, str(automation / "InferenceRunner.py"), "{session}"],
                    "result_schema": str(inference_schema),
                    "initial_peak_memory_mib": 32,
                    "max_memory_mib": 512,
                },
                "fixture.owned": {
                    "pool": "owned",
                    "argv": [sys.executable, str(automation / "SharedQueue/OwnedWorker.py"), "{session}"],
                    "result_schema": str(fixture_schema),
                    "initial_peak_memory_mib": 16,
                    "max_memory_mib": 256,
                },
            }
        }
    )
    config = client.write(
        {
            "state": str(client.root / "SupervisorState"),
            "controller": {"adapter": "a03", "store": str(client.root / "State")},
            "registry": str(registry),
            "worker": "supervisor:shared-fixture",
            "pools": {"inference": {"max_sessions": 1}, "owned": {"max_sessions": 1}},
            "stop_grace_seconds": 1,
            "poll_seconds": 0.1,
            "reserved_cpus": 0,
            "reserved_memory_mib": 0,
            "adaptive_limits": False,
        }
    )
    process = subprocess.Popen(
        [sys.executable, str(automation / "Supervisor.py"), "--config", str(config), "run", "--idle-seconds", "1", "--max-seconds", "45"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if marker.is_file() and client.state(work)["state"] == "completed":
                break
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=10)
                raise AssertionError(("supervisor exited before consuming shared work", stdout, stderr))
            time.sleep(0.1)
        else:
            raise AssertionError("shared work did not reach real worker processes")
        assert json.loads(marker.read_text(encoding="utf-8"))["job"] == owned
        completed = client.state(work)
        result_path = client.run("artifact", completed["result"])["path"]
        result = json.loads(Path(result_path).read_text(encoding="utf-8"))["result"]["records"]
        assert result["execution"]["fingerprint"] == completed["fingerprint"]
        assert result["semantic_qualification"] == "unverified"
        client.run("cancel-request", "supervised:owned", "--revision", "1")
        stdout, stderr = process.communicate(timeout=30)
        assert process.returncode == 0, (stdout, stderr)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)
    events = [json.loads(line) for line in stdout.splitlines()]
    assert any(event.get("event") == "finished" and event.get("job") == owned and event["receipt"]["stop_reason"] == "stale_lease" for event in events), events
    assert client.state(owned)["state"] == "rejected"
    assert not list((client.root / "SupervisorState/sessions").iterdir())
    if os.name == "posix":
        assert marker.with_suffix(".stopped").read_text(encoding="ascii") == str(json.loads(marker.read_text(encoding="utf-8"))["pid"])
    return {"actual_inference_runner": True, "owned_worker_stopped": True, "canonical_fingerprint_verified": True}
