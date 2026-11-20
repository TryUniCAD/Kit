# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO as ByteStream
from pathlib import Path as FilePath

from pytest import mark as TestMark

from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.json.Adapter import JsonAdapter
from interchange.Features.FeatureExtrude import ExtrudeEnd
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase
from tests.Convert.Solidworks.Core.NativeWrites.EndEvidence import EndEvidence
from tests.Convert.Solidworks.Core.NestedDocument import NestedDocument


# qualified scoped extents must retain their history through public and direct interchange writes
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("IsSuppressed", (False, True))
def TestScopedWrite(TmpPath: FilePath, IsNested: bool, IsSuppressed: bool) -> None:
    Document = EndEvidence("extrude", ExtrudeEnd.BLIND, IsSuppressed, True)
    if IsNested:
        Document = NestedDocument(AdapterCase("rectangle"), Document)
    Document.assert_valid()
    TargetPath = TmpPath / "Scoped.json"
    _ = WriteDocument(Document, TargetPath)
    assert OpenDocument(TargetPath) == Document
    Output = ByteStream()
    _ = JsonAdapter().write(Document, Output)
    assert OpenDocument(Output.getvalue(), source_format="interchange.json") == Document
