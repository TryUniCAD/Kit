from collections.abc import Mapping
from math import isclose as IsClose
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.AssertAxisRead import (
    AssertAxisRead,
)


# live typed parameter owners must agree with actual public line and relation identities after normal strict reading
def AssertRectRead(
    DocumentValue: CadDocument,
    WidthValue: float,
    HeightValue: float,
    NamesValue: tuple[str, str] = ("D1", "D2"),
) -> None:
    (SketchValue,) = DocumentValue.sketches
    ProfileId = SketchValue.attributes["native_object_id"]
    assert SketchValue.attributes["typed_line_loop"] is True
    assert SketchValue.attributes["typed_line_dimensions"] is True
    assert len(SketchValue.entities) == 4
    EntityIds = tuple(Entity.id for Entity in SketchValue.entities)
    assert EntityIds == tuple(
        f"sldprt:sketch:{ProfileId}:line:{Index + 1}" for Index in range(4)
    )
    assert SketchValue.closed_profile_entity_ids == (EntityIds,)
    assert SketchValue.parameter_ids == tuple(
        f"sldprt:parameter:{ProfileId}:{NameValue}" for NameValue in NamesValue
    )
    Parameters = {Parameter.id: Parameter for Parameter in DocumentValue.parameters}
    for ParamId, Expected in zip(
        SketchValue.parameter_ids, (WidthValue, HeightValue), strict=True
    ):
        Parameter = Parameters[ParamId]
        assert (
            Parameter.value.kind == ValueKind.KLength and Parameter.value.unit == "mm"
        )
        assert Parameter.role == ParameterRole.KDriving and Parameter.expression is None
        assert IsClose(
            CastValue(float, Parameter.value.value),
            Expected,
            rel_tol=1e-9,
            abs_tol=1e-9,
        )
        OwnerValue = CastValue(
            Mapping[str, object], Parameter.attributes["typed_archive_owner"]
        )
        assert (
            OwnerValue["class"] == "moLengthParameter_c"
            and OwnerValue["value_field"] == "f58"
        )
        assert OwnerValue["field_span"] is False
        assert all(
            type(OwnerValue[NameValue]) is int
            for NameValue in (
                "dimension_id",
                "dimension_index",
                "display_index",
                "handle_index",
                "object_index",
            )
        )
    AssertAxisRead(SketchValue)
    EvidenceValue = CastValue(
        Mapping[str, object],
        DocumentValue.metadata["solidworks.typed_resolved_semantics"],
    )
    assert EvidenceValue["line_dimension_profiles"] == (ProfileId,)
    assert EvidenceValue["public_writer_qualified"] is False
    DocumentValue.assert_valid()
