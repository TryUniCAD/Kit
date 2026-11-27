# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.Research.SupervisorClient import KRepoRoot as KSourceRoot
from tests.Research.Inference.Authoring.Pipeline.RunPipeline import RunPipeline

# the retained native control must come from its actual committed git object
KNativeSource = (
    "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
)


# fixture input binding crosses the controller process using a real native document
def BindNative(TmpPath: FilePath, StorePath: FilePath) -> None:
    Snapshot = RunProcess(
        ["git", "show", "HEAD:" + KNativeSource],
        cwd=KSourceRoot,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert Snapshot.returncode == 0, Snapshot.stderr.decode("utf-8", errors="replace")
    NativePath = TmpPath / "NativeControl.f3d"
    _ = NativePath.write_bytes(Snapshot.stdout)
    _ = RunPipeline(
        KSourceRoot / "re/automation/Controller.py",
        "--store",
        StorePath,
        "bind",
        "fixture-native",
        NativePath,
    )
