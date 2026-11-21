# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from sys import executable
from time import monotonic

from InferenceGrid.Authoring.AuthorConfig import AuthorConfig
from InferenceGrid.CatalogueBatch import RunSupervisor
from InferenceGrid.Resume import BindGrid
from Ledger import Ledger
from Records import digest, read_record
from Sessions import write_private


# existing controller pools leases and application resources own all development stages
def DevelopmentConfig(Directory, SourceRoot, HostPath):
    ConfigPath, Resources = AuthorConfig(Directory, SourceRoot, 1, None, HostPath)
    Config = read_record(ConfigPath)
    RegistryPath = Path(Config["registry"])
    Registry = read_record(RegistryPath)
    SchemaPath = Directory / "AuthorResultSchema.json"
    for Kind, Mode in (
        ("builder.generate", "generate"),
        ("builder.native", "native"),
        ("builder.verify", "verify"),
        ("builder.capture", "capture"),
    ):
        Native = Mode in {"native", "capture"}
        Registry["runners"][Kind] = {
            "pool": "authoring-solidworks" if Native else "inference",
            "argv": [
                executable,
                "-B",
                str(
                    SourceRoot
                    / "re/automation/InferenceGrid/BuilderDevelopment/Worker.py"
                ),
                "--mode",
                Mode,
                "--directory",
                str(Directory),
                "{session}",
            ],
            "result_schema": str(SchemaPath),
            "threads": 1,
            "initial_peak_memory_mib": 2048 if Native else 256,
            "max_memory_mib": 8192 if Native else 1024,
        }
    write_private(RegistryPath, Registry)
    return ConfigPath, Resources


# bound records are immutable controller inputs rather than mutable files in a candidate workspace
def SubmitStage(Directory, Job, Stage, Inputs, Dependencies=None, Resource=None):
    with Ledger(Directory / "Store") as State:
        Bindings = {}
        for Role, Value in Inputs.items():
            Pin = State.objects.put_record(
                Value if isinstance(Value, dict) else {"builder_value": Value}
            )
            Binding = "builder-input:" + Pin
            BindGrid(State, Binding, Pin)
            Bindings[Role] = Binding
        Identity = (
            "builder-" + Stage + ":" + digest([Job["id"], Inputs, Dependencies or {}])
        )
        Definition = {
            "id": Identity,
            "kind": "builder." + Stage,
            "tool_version": Job["source_revision"],
            "rule_version": "builder-development@1",
            "inputs": {**Bindings, **(Dependencies or {})},
            "options": {"job_sha256": digest(Job)},
            "max_attempts": 1,
            "timeout_seconds": min(86400, Job["limits"]["seconds"]),
        }
        if Resource:
            Definition["resources"] = [Resource]
        Parents = sorted({Item["dependency"] for Item in (Dependencies or {}).values()})
        if Parents:
            Definition["depends_on"] = Parents
        State.submit_many([Definition])
    return Identity


# the existing metadata transport requires an object even for typed arrays and scalar stage inputs
def UnwrapInput(Value):
    return Value["builder_value"] if set(Value) == {"builder_value"} else Value


# immutable receipts are the authority for resumed work and never a worker's success string alone
def ReadStage(Directory, Identity):
    with Ledger(Directory / "Store") as State:
        Job = State.status(Identity)["jobs"][0]
        if Job["state"] != "completed":
            return {
                "status": Job["state"],
                "classification": "execution_incomplete",
                "reason": Job.get("reason"),
                "job": Job,
            }
        State.verify_result(Job["result"])
        Result = read_record(State.objects.path(Job["result"]))
        return {
            "status": "completed",
            "records": Result["result"]["records"],
            "receipt": Job["receipt"],
            "result_sha256": Job["result"],
            "job": Job,
        }


# running the existing supervisor retains its pause recovery resource and descendant ownership semantics
def DriveStage(Directory, SourceRoot, ConfigPath, Identity, Seconds):
    Existing = ReadStage(Directory, Identity)
    if Existing["status"] == "completed":
        return Existing
    Failure = RunSupervisor(
        Directory,
        SourceRoot,
        ConfigPath,
        max(1, int(Seconds)),
        "Authoring",
        Resume=(Directory / "AuthoringSupervisor.log").exists(),
    )
    Result = ReadStage(Directory, Identity)
    if Failure:
        Result["supervisor_failure"] = Failure
    return Result


# dependent decoding cannot run before an accepted qualified native capture artifact exists
def SubmitDecoder(Directory, Job, Capture, RecoveryEpoch=0):
    Identity = "builder-decode:" + digest([Job["id"], Capture, RecoveryEpoch])
    with Ledger(Directory / "Store") as State:
        State.submit_many(
            [
                {
                    "id": Identity,
                    "kind": "catalogue.decode",
                    "tool_version": Job["source_revision"],
                    "rule_version": "builder-samples@1",
                    "depends_on": [Capture],
                    "inputs": {
                        "native.accepted": {"dependency": Capture},
                        "bundle": {"dependency": Capture, "artifact": "bundle"},
                    },
                    "options": {"application": "solidworks"},
                }
            ]
        )
    return Identity
