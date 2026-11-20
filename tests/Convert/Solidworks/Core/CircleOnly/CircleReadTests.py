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
from interchange.serialization.JsonCodec import DumpJson, LoadJson
from tests.Convert.Solidworks.Core.CircleOnly.AssertCircle import AssertCircle
from tests.Convert.Solidworks.Core.CircleOnly.Samples import KCases, ReadCircleInput


# both normal geometry modes must expose the same complete standalone editing semantics
@TestMark.parametrize(("CaseName", "Radius", "PlaneId", "DisplayUnit"), KCases)
@TestMark.parametrize("IncludeBrep", (False, True))
@TestMark.parametrize("StrictMode", (False, True))
def CheckCircleOnly(
    CaseName: str,
    Radius: float,
    PlaneId: int,
    DisplayUnit: str,
    IncludeBrep: bool,
    StrictMode: bool,
) -> None:
    SourceBytes = ReadCircleInput(CaseName)
    Document = OpenDocument(
        SourceBytes,
        SourceFormat=KPartFormatId,
        IncludeBrep=IncludeBrep,
        IncludeTess=False,
        StrictMode=StrictMode,
    )
    AssertCircle(Document, Radius, PlaneId, DisplayUnit)
    assert LoadJson(DumpJson(Document)) == Document
    assert ReadCircleInput(CaseName) == SourceBytes
