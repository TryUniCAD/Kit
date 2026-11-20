# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert.Formats.Fusion.DocumentRead import ReadFusionDoc
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ParameterRole


# existing radial modes and unqualified angular roles remain independent of the linear role correction
@MarkTests.parametrize(
    "FileStem,ExpectedRole",
    (
        ("radius_driving", ParameterRole.KDriving),
        ("radius_reference", ParameterRole.KReference),
        ("diameter_driving", ParameterRole.KDriving),
        ("diameter_reference", ParameterRole.KReference),
        ("angle_driving", ParameterRole.KReference),
    ),
)
def TestRadialRole(FileStem: str, ExpectedRole: ParameterRole) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    Document = ReadFusionDoc(
        RootPath / "re/Fusion/Study/dimcontrols-2a0d0bdbc8a6" / f"{FileStem}.f3d"
    )
    Parameters = {Value.id: Value for Value in Document.parameters}
    Dimensions = tuple(
        Relation
        for SketchValue in Document.sketches
        for Relation in SketchValue.constraints
        if Relation.parameter_id
    )
    assert len(Dimensions) == 1
    ParameterId = Dimensions[0].parameter_id
    assert ParameterId is not None
    assert Parameters[ParameterId].role is ExpectedRole
    assert CadDocument.from_json(Document.to_json()) == Document
