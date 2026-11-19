# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.JobClient import JobClient


# real intake commands must resolve relative input paths from the request directory
def WriteBindings(
    Manifest: FilePath, FirstName: str, OtherName: str, SecondName: str = "right"
) -> None:
    _ = Manifest.write_text(
        EncodeJson(
            {
                "bindings": [
                    {"name": "left", "file": FirstName},
                    {"name": SecondName, "file": OtherName},
                ]
            }
        ),
        encoding="utf-8",
    )


# snapshots expose whether a batch leaves existing dependents in one consistent generation
def ReadBoundJob(Client: JobClient) -> dict[str, object]:
    return CastValue(
        dict[str, object],
        ParseJson(Client.RunCli("status", "--job", "binding-witness"))["jobs"][0],
    )


# a complete batch must publish both inputs and refresh each dependent snapshot once
def CheckBatchBind(TmpPath: FilePath) -> None:
    Client = JobClient(TmpPath)
    InputPath = TmpPath / "Inputs"
    InputPath.mkdir()
    for NameValue in ("left-a", "left-b", "right-a", "right-b"):
        _ = (InputPath / NameValue).write_text(NameValue, encoding="utf-8")
    JobPath = TmpPath / "Job.json"
    _ = JobPath.write_text(
        EncodeJson(
            {
                "id": "binding-witness",
                "kind": "fixture.inspect",
                "inputs": {"left": "left", "right": "right"},
                "rule_version": "rule@1",
                "tool_version": "tool@1",
            }
        ),
        encoding="utf-8",
    )
    _ = Client.RunCli("submit", str(JobPath))
    Manifest = InputPath / "Bindings.json"
    WriteBindings(Manifest, "left-a", "right-a")
    FirstBind = ParseJson(Client.RunCli("bind-batch", str(Manifest)))
    assert FirstBind == {
        "bindings": [
            {"name": "left", "sha256": DigestBytes(b"left-a").hexdigest()},
            {"name": "right", "sha256": DigestBytes(b"right-a").hexdigest()},
        ]
    }
    Initial = ReadBoundJob(Client)
    assert Initial["state"] == "queued"
    for OtherName, SecondName in (("missing", "right"), ("right-b", "left")):
        WriteBindings(Manifest, "left-b", OtherName, SecondName)
        _ = Client.RunCli("bind-batch", str(Manifest), ExitCode=1)
        assert ReadBoundJob(Client) == Initial
    WriteBindings(Manifest, "left-b", "right-b")
    _ = Client.RunCli("bind-batch", str(Manifest))
    Updated = ReadBoundJob(Client)
    assert Updated["state"] == "queued"
    assert Updated["fingerprint"] != Initial["fingerprint"]
    assert (
        CastValue(int, Updated["generation"])
        == CastValue(int, Initial["generation"]) + 1
    )
