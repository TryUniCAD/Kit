# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Research.Archives.FusionBossRequest.MoveSettingsRole import MoveObserver
from tests.Research.Archives.FusionBossRequest.ObserverProgram import KObserverProgram
from tests.Research.Archives.FusionBossRequest.RaiseSettingsRank import RaiseRank
from tests.Research.Archives.FusionBossRequest.RedirectSnap import RedirectSnap


# observer and snapshot mutations must round trip across native archives before the expected refusal
def CheckObsReject(
    MirrorRoot: FilePath, WorkPath: FilePath, ArchiveBytes: bytes
) -> None:
    Model = ReadDocument(ArchiveBytes)
    Graph = BuildGraph(Model)
    Mutated = (
        (WorkPath / "WrongSnapshot.f3d", RedirectSnap(Model, Graph)),
        (WorkPath / "WrongRole.f3d", MoveObserver(Model, Graph)),
        (WorkPath / "WrongRank.f3d", RaiseRank(Model, Graph)),
    )
    for OutputPath, Variation in Mutated:
        Payload = EmitParsed(Variation)
        assert Payload != ArchiveBytes
        _ = OutputPath.write_bytes(Payload)
    Result = RunProcess(
        [
            PythonExe,
            "-I",
            "-B",
            "-c",
            KObserverProgram,
            str(MirrorRoot),
            *(str(OutputPath) for OutputPath, _ in Mutated),
        ],
        cwd=MirrorRoot,
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=120,
    )
    assert Result.returncode == 0, Result.stderr
