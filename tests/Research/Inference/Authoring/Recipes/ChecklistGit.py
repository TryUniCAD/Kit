# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.Research.SupervisorClient import KRepoRoot


# independent checkouts exercise publication and pickup without writing the shared repository
def CloneChecklist(Source: FilePath, Target: FilePath) -> None:
    _ = RunProcess(
        ["git", "clone", "--shared", "--no-checkout", str(Source), str(Target)],
        capture_output=True,
        check=True,
        timeout=120,
    )
    _ = RunGit(
        Target,
        "sparse-checkout",
        "set",
        "--no-cone",
        "/re/automation/",
        "/re/CatalogueChecklist/",
        "/src/",
        "/pyproject.toml",
        "/uv.lock",
    )
    _ = RunGit(Target, "checkout", "--detach", RunGit(Source, "rev-parse", "HEAD"))


# fixture commits need an isolated identity on every hosted runner
def RunGit(RootPath: FilePath, *ArgsValue: str) -> str:
    return RunProcess(
        [
            "git",
            "-c",
            "user.name=Kit integration",
            "-c",
            "user.email=kit-integration@example.invalid",
            *ArgsValue,
        ],
        cwd=RootPath,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    ).stdout.strip()


# an isolated publisher can commit fixture records while the actual checkout stays clean
def MakePublisher(RootPath: FilePath) -> FilePath:
    Publisher = RootPath / "Publisher"
    CloneChecklist(KRepoRoot, Publisher)
    return Publisher
