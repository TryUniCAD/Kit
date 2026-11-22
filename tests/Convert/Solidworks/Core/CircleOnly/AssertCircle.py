# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Severity
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from tests.Convert.Solidworks.Core.CircleOnly.AssertSupport import AssertSupport


# the public document must retain the independent native circle diameter and origin ownership
def AssertCircle(
    Document: CadDocument, Radius: float, PlaneId: int, DisplayUnit: str
) -> None:
    Document.assert_valid()
    assert Document.bodies == () and Document.brep is None
    (PropertyInfo,) = Document.diagnostics
    assert PropertyInfo.code == "solidworks.part_text_properties_unavailable"
    assert PropertyInfo.severity == Severity.INFO
    assert PropertyInfo.message == "part properties require an empty compatible native manager"
    assert Document.metadata["source_display_units"] == DisplayUnit
    (SketchValue,) = Document.sketches
    Circle, Origin = SketchValue.entities
    assert isinstance(Circle.geometry, CircleGeometry) and not Circle.construction
    assert Circle.geometry.center == PlaneVector(0, 0)
    assert Circle.geometry.radius == Radius
    assert (
        isinstance(Origin.geometry, PointGeometry)
        and Origin.construction
        and Origin.fixed
    )
    assert Origin.geometry.point == PlaneVector(0, 0)
    assert SketchValue.closed_profile_entity_ids == ((Circle.id,),)
    Diameter, Coincidence = SketchValue.constraints
    assert Diameter.kind == "diameter" and Diameter.driving is True
    assert [(Entry.entity_id, Entry.point) for Entry in Diameter.references] == [
        (Circle.id, "")
    ]
    assert Coincidence.kind == "coincident"
    assert [(Entry.entity_id, Entry.point) for Entry in Coincidence.references] == [
        (Origin.id, ""),
        (Circle.id, "center"),
    ]
    (Parameter,) = tuple(
        Value for Value in Document.parameters if Value.id == Diameter.parameter_id
    )
    assert Parameter.value.unit == "mm" and Parameter.value.value == Radius * 2
    assert SketchValue.parameter_ids == (Parameter.id,)
    AssertSupport(Document, PlaneId)
    assert isinstance(SketchValue.attributes["native_profile_state"], int)
    for Record in (
        SketchValue,
        Circle,
        Origin,
        Diameter,
        Coincidence,
        Parameter,
    ):
        assert Record.provenance is not None and Record.provenance.spans
        assert all(
            SourceSpan.stream == "Contents/Config-0-ResolvedFeatures"
            and SourceSpan.length > 0
            for SourceSpan in Record.provenance.spans
        )
