# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path

from ProcessClient import Client, job


# progress polling must not hash large payloads while holding a controller write transaction
def check_metadata(root):
    client = Client(root / "Metadata")
    source = client.root / "LargeInput.bin"
    source.write_bytes(b"original CAD evidence" * 1024 * 1024)
    bound = client.run("bind", "evidence:large", source)
    identity = client.enqueue(
        "metadata:reader", [job("local:reader", inputs={"source": "evidence:large"})]
    )["jobs"]["local:reader"]
    claimed, lease = client.claim("MetadataClaim")
    assert claimed == identity
    client.finish(lease)
    blob = Path(client.run("artifact", bound["sha256"])["path"])
    blob.write_bytes(b"corrupt evidence must still fail integrity inspection")
    for arguments in ((), ("--request", "metadata:reader")):
        report = client.run("queue-status", *arguments)
        assert report["scope"] == "queue_metadata"
        assert report["acceptance_verified"] is False
        assert report["artifact_bytes_hashed"] == 0
        assert report["reused_jobs"] == 1
    error = client.run("status", "--job", identity, code=1)
    assert "integrity" in error or "hash" in error, error
    return {
        "metadata_payload_hashes": 0,
        "acceptance_not_claimed": True,
        "corrupt_evidence_refused": True,
    }
