# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path

from Corpus import git
from Pilot.PilotFiles import FileDigest
from Pilot.RuntimePins import RuntimePins


# frozen tracked runtime bytes make every resumed attempt attributable to one source revision
def SourcePins(SourceRoot, Revision):
    SourceRoot = Path(SourceRoot).resolve()
    if git(SourceRoot, "rev-parse", "HEAD").decode().strip() != Revision:
        raise ValueError("pilot source revision differs from the checkout head")
    if git(SourceRoot, "status", "--porcelain", "--untracked-files=no").strip():
        raise ValueError("pilot source must have no tracked modifications")
    Untracked = (
        git(
            SourceRoot,
            "ls-files",
            "--others",
            "-z",
            "--",
            "src",
            "re/automation",
            "re/Fusion/Study",
        )
        .decode()
        .split("\0")
    )
    if any(Relative.endswith((".py", ".json")) for Relative in Untracked if Relative):
        raise ValueError("pilot source has untracked runtime modules or configuration")
    Paths = (
        git(
            SourceRoot,
            "ls-files",
            "-z",
            "--",
            "src",
            "re/automation",
            "re/Fusion/Study",
            "uv.lock",
            "pyproject.toml",
        )
        .decode()
        .split("\0")
    )
    return {
        Relative: FileDigest(SourceRoot / Relative)
        for Relative in sorted(Paths)
        if Relative
        and (
            Relative.endswith(".py")
            or (Relative.startswith("src/") and Relative.endswith(".json"))
            or Relative in {"uv.lock", "pyproject.toml"}
        )
    }


# runtime pin changes must stop unattended work rather than silently change its evidence authority
def VerifyPins(Manifest):
    RootPath = Path(Manifest["source"])
    if SourcePins(RootPath, Manifest["source_revision"]) != Manifest["source_files"]:
        raise ValueError("pilot runtime source bytes changed")
    if (
        FileDigest(Manifest["python_base_executable"])
        != Manifest["python_base_executable_sha256"]
    ):
        raise ValueError("pilot base interpreter bytes changed")
    if RuntimePins() != Manifest["runtime_packages"]:
        raise ValueError("pilot installed package versions changed")
    for KeyName in ("config", "registry", "schema", "schedule"):
        if FileDigest(Manifest[KeyName]) != Manifest[KeyName + "_sha256"]:
            raise ValueError(f"pilot {KeyName} bytes changed")
    for PinValue in Manifest["input_pins"].values():
        if FileDigest(PinValue["path"]) != PinValue["sha256"]:
            raise ValueError("pilot archived input bytes changed")
