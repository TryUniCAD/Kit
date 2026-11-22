# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from time import monotonic

from InferenceGrid.BuilderDevelopment.Generation.GenerationPacket import (
    BuildPrompt,
    WriteArtifact,
)
from InferenceGrid.BuilderDevelopment.Generation.GenerationPaths import OwnedPath


# reused choices receive fresh run artifacts without inventing a provider reservation or native acceptance
def PublishReuse(
    Result, Packet, PacketPin, Options, Directory, Budget, Schema, Started
):
    Target = OwnedPath(Directory, Budget["run_root"])
    Target.mkdir(mode=0o700, parents=True, exist_ok=True)
    Target = OwnedPath(Target, Budget["run_root"])
    if any(Target.iterdir()):
        raise ValueError("generation requires a fresh private attempt directory")
    Artifacts = {}
    for Name, Value in (
        ("Packet.json", Packet),
        ("Schema.json", Schema),
        ("Candidate.json", Result["program"]),
        ("Reuse.json", Result["cache"]),
        (
            "Request.json",
            {
                "schema_version": 1,
                "packet_sha256": PacketPin,
                "provider": Options.provider,
                "auth": Options.auth,
                "model": Options.model,
                "reservation": None,
                "tools_enabled": False,
                "reserved_qualification_disclosed": False,
                "reused_generation": True,
            },
        ),
    ):
        Artifacts[Name] = WriteArtifact(Target / Name, Value)
    Prompt = BuildPrompt(Packet).encode("utf-8")
    with (Target / "Prompt.txt").open("xb") as Output:
        Output.write(Prompt)
    Artifacts["prompt"] = {
        "path": str(Target / "Prompt.txt"),
        "size_bytes": len(Prompt),
        "sha256": sha256(Prompt).hexdigest(),
    }
    Result.update(elapsed_seconds=monotonic() - Started, artifact_paths=Artifacts)
    WriteArtifact(Target / "Generation.json", Result)
    return Result
