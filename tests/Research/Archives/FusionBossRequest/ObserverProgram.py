# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# the fresh decoder must prove each altered archive reaches the real observer check
KObserverProgram = """
from pathlib import Path
import sys

sys.path[:0] = [
    str(Path(sys.argv[1]) / "src"),
    str(Path(sys.argv[1]) / "re/automation"),
    str(Path(sys.argv[1]) / "re/solidworks/WriterResearch"),
    str(Path(sys.argv[1]) / "re/Fusion/Reconstruction/DimensionAuthoring"),
]
from BossSettingsOrder import check_settings_order
from SourceBossReplay import SNAPSHOT_SOURCE, SNAPSHOT_BLOB, SNAPSHOT_SHA256, load_pinned_helper
from SourceBossSnapshot import snapshot_evidence
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


# failures must come from the observer contract after typed archive decoding succeeds
def RejectObservers(ArchivePaths):
    for ArchivePath in ArchivePaths:
        Graph = BuildGraph(ReadDocument(Path(ArchivePath).read_bytes()))
        try:
            check_settings_order(Graph)
        except ValueError as Failure:
            assert str(Failure) == "P03 generated settings observers differ from the browser-first schedule"
        else:
            raise AssertionError(f"observer check admitted {Path(ArchivePath).name}")


# snapshot refusal must come from the actual owner verifier after native decoding succeeds
def RejectSnapshot(CodeRoot, ArchivePath):
    Builder, PinValue = load_pinned_helper(
        Path(CodeRoot) / "SnapshotBuilder.py", SNAPSHOT_SOURCE,
        SNAPSHOT_BLOB, SNAPSHOT_SHA256,
    )
    assert PinValue["sha256"] == SNAPSHOT_SHA256
    Model = ReadDocument(Path(ArchivePath).read_bytes())
    try:
        snapshot_evidence(Model, Builder)
    except ValueError as Failure:
        assert str(Failure) == "Saved snapshot roots do not resolve to their expected Design owners"
    else:
        raise AssertionError("snapshot check admitted a foreign topology cache")


RejectSnapshot(sys.argv[1], sys.argv[2])
RejectObservers(sys.argv[3:])
"""
