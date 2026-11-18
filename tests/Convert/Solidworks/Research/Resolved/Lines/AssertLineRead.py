from collections.abc import Mapping
from math import isclose as IsClose
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from tests.Convert.Solidworks.Research.Resolved.Lines.AssertLineBox import AssertLineBox


# exact public endpoints loop ids ownership and bounds must agree with independent neutral geometry
def AssertLineRead(
    Document: CadDocument,
    VerticesValue: tuple[tuple[float, float], ...],
    DepthValue: float,
) -> None:
    (SketchValue,) = Document.sketches
    NativeId = SketchValue.attributes["native_object_id"]
    IdsValue = tuple(
        f"sldprt:sketch:{NativeId}:line:{Index + 1}"
        for Index in range(len(VerticesValue))
    )
    assert tuple(Entity.id for Entity in SketchValue.entities) == IdsValue
    assert SketchValue.closed_profile_entity_ids == (IdsValue,)
    assert SketchValue.constraints == ()
    assert SketchValue.parameter_ids == ()
    assert SketchValue.attributes["typed_line_loop"] is True
    Points = CastValue(
        tuple[Mapping[str, object], ...], SketchValue.attributes["native_point_rows"]
    )
    assert len(Points) == len(VerticesValue)
    for Index, (Entity, StartValue, EndValue) in enumerate(
        zip(
            SketchValue.entities,
            VerticesValue,
            VerticesValue[1:] + VerticesValue[:1],
            strict=True,
        )
    ):
        assert Entity.kind == GeometryKind.KLine and isinstance(
            Entity.geometry, LineGeometry
        )
        Actual = (
            Entity.geometry.start.x,
            Entity.geometry.start.y,
            Entity.geometry.end.x,
            Entity.geometry.end.y,
        )
        assert all(
            IsClose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-12)
            for ActualValue, ExpectedValue in zip(
                Actual, StartValue + EndValue, strict=True
            )
        )
        EntityOwner = CastValue(
            Mapping[str, object], Entity.attributes["typed_archive_owner"]
        )
        assert EntityOwner["class"] == "sgSketch"
        assert EntityOwner["embedded_array"] == "lines"
        assert EntityOwner["row_index"] == Index
        assert EntityOwner["field_span"] is False
        assert (
            Entity.provenance is not None
            and Entity.provenance.spans[0].record_kind == "typed-archive-object"
        )
        assert Points[Index]["native_creation_id"] == Index + 1
        Handles = CastValue(
            tuple[Mapping[str, object], ...], Points[Index]["line_handles"]
        )
        HandleFields = tuple(
            CastValue(Mapping[str, object], Handle["fields"]) for Handle in Handles
        )
        assert {
            Value["f18"] if Value["idx"] == 30591 else Value["idx"]
            for Value in HandleFields
        } == {
            Index,
            (Index - 1) % len(VerticesValue),
        }
    Evidence = CastValue(
        Mapping[str, object], Document.metadata["solidworks.typed_resolved_semantics"]
    )
    assert Evidence["typed_geometry_projection"] is True
    assert Evidence["line_loop_profiles"] == (NativeId,)
    assert Evidence["public_writer_qualified"] is False
    AssertLineBox(Document, VerticesValue, DepthValue)
