# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
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
from tests.Convert.Api.Fusion.Native.DimensionRoleArchive import AlterDimRoles


# changed native controls cannot promote reference shared unsupported or conflicting dimension parameters
@MarkTests.parametrize(
    "CaseName", ("reference", "shared", "unsupported", "unknown-flag", "binding")
)
def TestRoleGuards(CaseName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    Source = (
        RootPath
        / "re/automation/PairedCaptures/P01/fusion-5dc3245eb59c/P01-fusion-baseline-a.f3d"
    )
    Document = ReadFusionDoc(AlterDimRoles(Source, CaseName))
    Parameters = {Value.name: Value for Value in Document.parameters}
    assert Parameters["width_mm"].role is ParameterRole.KReference
    if CaseName == "reference":
        assert Parameters["height_mm"].role is ParameterRole.KDriving
        Dimensions = tuple(
            Relation
            for SketchValue in Document.sketches
            for Relation in SketchValue.constraints
            if Relation.parameter_id
        )
        assert [Relation.driving for Relation in Dimensions] == [False, True]
    else:
        assert Parameters["height_mm"].role is ParameterRole.KReference
        if CaseName != "shared":
            assert any(
                Value.code.startswith("fusion.sketch.dimension.")
                for Value in Document.diagnostics
            )
    assert CadDocument.from_json(Document.to_json()) == Document
