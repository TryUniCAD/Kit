# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pytest import mark as TestMark

from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.api.ApiOpen import OpenDocument
from tests.Convert.Solidworks.Core.CircleOnly.AlterCircle import AlterCircle


# decoded solid geometry contradicts the sketch only history and must prevent body removal
@TestMark.parametrize("StrictMode", (False, True))
def CheckBodyGuard(StrictMode: bool) -> None:
    Document = OpenDocument(
        AlterCircle("body"),
        SourceFormat=KPartFormatId,
        IncludeBrep=True,
        IncludeTess=False,
        StrictMode=StrictMode,
    )
    assert Document.brep is not None and len(Document.brep.bodies) == 1
    assert len(Document.bodies) == 1
    assert any(
        Entry.code == "sldprt.circular_sketch_unresolved"
        for Entry in Document.diagnostics
    )
    assert all(
        "native_profile_state" not in Sketch.attributes for Sketch in Document.sketches
    )


# authentic extra authored history cannot acquire standalone semantics from an empty body configuration
@TestMark.parametrize("IncludeBrep", (False, True))
@TestMark.parametrize("StrictMode", (False, True))
def CheckHistGuard(IncludeBrep: bool, StrictMode: bool) -> None:
    Document = OpenDocument(
        AlterCircle("history"),
        SourceFormat=KPartFormatId,
        IncludeBrep=IncludeBrep,
        IncludeTess=False,
        StrictMode=StrictMode,
    )
    assert len(Document.bodies) == 1
    assert all(
        "native_profile_state" not in Sketch.attributes for Sketch in Document.sketches
    )
