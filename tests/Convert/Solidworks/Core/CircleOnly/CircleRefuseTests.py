# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pytest import mark as TestMark

from convert.api.ApiOpen import OpenDocument
from convert.adapters.solidworks.Container.Format import KPartFormatId
from tests.Convert.Solidworks.Core.CircleOnly.AlterCircle import AlterCircle
from tests.Convert.Solidworks.Core.CircleOnly.Samples import KRepoRoot


# contradictions must retain an explicit unresolved result instead of promoting guessed circular semantics
@TestMark.parametrize("ModeValue", ("diameter", "support", "flags", "footer"))
def CheckRefusal(ModeValue: str) -> None:
    Document = OpenDocument(
        AlterCircle(ModeValue),
        SourceFormat=KPartFormatId,
        IncludeBrep=False,
        IncludeTess=False,
    )
    assert any(
        Entry.code == "sldprt.circular_sketch_unresolved"
        for Entry in Document.diagnostics
    )
    assert all(len(Sketch.constraints) == 1 for Sketch in Document.sketches)


# actual solid and cut histories must retain their bodies through the standalone candidate boundary
@TestMark.parametrize(
    "CaseName",
    (
        "P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT",
        "P04/solidworks-c1986308375a/P04-solidworks-baseline-a.SLDPRT",
    ),
)
@TestMark.parametrize("IncludeBrep", (False, True))
def CheckSolidRead(CaseName: str, IncludeBrep: bool) -> None:
    SourcePath = KRepoRoot / "re/automation/PairedCaptures" / CaseName
    SourceBytes = SourcePath.read_bytes()
    Document = OpenDocument(SourcePath, IncludeBrep=IncludeBrep, IncludeTess=False)
    assert len(Document.bodies) == 1
    assert not any(
        Entry.code == "sldprt.circular_sketch_unresolved"
        for Entry in Document.diagnostics
    )
    assert any(Entry.operation == "join" for Entry in Document.feature_timeline)
    if CaseName.startswith("P04"):
        assert any(Entry.operation == "cut" for Entry in Document.feature_timeline)
    assert SourcePath.read_bytes() == SourceBytes
