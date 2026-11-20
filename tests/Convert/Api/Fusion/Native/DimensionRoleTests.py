# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as ParseJson
from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert.Formats.Fusion.DocumentRead import ReadFusionDoc
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ParameterRole
from tests.Convert.Api.Fusion.Native.DiscoveryRoleCases import KDiscoveryCases


# all measured discovery variants must preserve role ownership through native decoding and neutral serialization
@MarkTests.parametrize("RecipeName,VariantName", KDiscoveryCases)
def TestDimDrivers(RecipeName: str, VariantName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    FolderName = {"P01": "fusion-5dc3245eb59c", "P03": "fusion-8d53584027ff"}[
        RecipeName
    ]
    CapturePath = RootPath / "re/automation/PairedCaptures" / RecipeName / FolderName
    FileName = f"{RecipeName}-fusion-{VariantName}.f3d"
    Receipt = ParseJson((CapturePath / "receipt.json").read_text())
    Expected = next(
        Value["sha256"]
        for Value in Receipt["native_files"]
        if Value["file"] == FileName
    )
    Payload = (CapturePath / FileName).read_bytes()
    assert HashBytes(Payload).hexdigest() == Expected
    Document = ReadFusionDoc(Payload)
    Parameters = {Value.id: Value for Value in Document.parameters}
    Dimensions = tuple(
        Relation
        for SketchValue in Document.sketches
        for Relation in SketchValue.constraints
        if Relation.parameter_id is not None
    )
    assert len(Dimensions) == 2
    Drivers = tuple(
        Parameters[Relation.parameter_id]
        for Relation in Dimensions
        if Relation.parameter_id is not None
    )
    assert {Value.name for Value in Drivers} == {
        "width_mm",
        "height_mm",
    }
    assert all(Relation.driving is True for Relation in Dimensions)
    assert all(Value.role is ParameterRole.KDriving for Value in Drivers)
    assert len({Value.owner_id for Value in Drivers}) == 1
    assert CadDocument.from_json(Document.to_json()) == Document
