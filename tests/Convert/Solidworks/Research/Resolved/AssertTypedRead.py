from typing import cast as CastValue

from interchange import CadDocument, ExtrusionFeature


# a public neutral feature must retain its actual typed parameter and profile owners without full graph claims
def AssertTypedRead(Document: CadDocument, DepthValue: float) -> None:
    Evidence = CastValue(
        dict[str, object], Document.metadata["solidworks.typed_resolved_semantics"]
    )
    assert Evidence["status"] == "supplemented" and Evidence["archive_version"] == 19000
    assert Evidence["full_linked_graph"] is Evidence["typed_assembly_mates"] is False
    assert Evidence["typed_geometry_projection"] is True
    (OwnerValue,) = CastValue(tuple[dict[str, object], ...], Evidence["extrusions"])
    NativeId, ProfileId = OwnerValue["feature_id"], OwnerValue["profile_id"]
    assert Evidence["line_loop_profiles"] == (ProfileId,)
    (Feature,) = tuple(
        ItemValue
        for ItemValue in Document.feature_timeline
        if ItemValue.id == f"sldprt:feature:{NativeId}"
    )
    assert Feature.name == "Boss-Extrude1"
    assert Feature.input_feature_ids == (f"sldprt:feature:{ProfileId}",)
    assert (
        isinstance(Feature.definition, ExtrusionFeature)
        and Feature.definition.length.value == DepthValue * 1000
    )
    (Parameter,) = tuple(
        ItemValue
        for ItemValue in Document.parameters
        if ItemValue.owner_id == Feature.id
        and ItemValue.name == OwnerValue["parameter_name"]
    )
    assert Parameter.value.value == DepthValue * 1000 and Parameter.value.unit == "mm"
    assert Parameter.role.value == "driving"
    ParamOwner = CastValue(
        dict[str, object], Parameter.attributes["typed_archive_owner"]
    )
    assert (
        ParamOwner["class"] == "moLengthParameter_c"
        and ParamOwner["value_field"] == "f58"
    )
    assert ParamOwner["dimension_id"] != NativeId and ParamOwner["field_span"] is False
    assert Parameter.provenance is not None and len(Parameter.provenance.spans) == 1
    (SpanValue,) = Parameter.provenance.spans
    assert (
        SpanValue.stream == ParamOwner["stream"]
        and SpanValue.offset == ParamOwner["offset"]
    )
    OffsetValue, EndValue = ParamOwner["offset"], ParamOwner["end"]
    assert type(OffsetValue) is int and type(EndValue) is int
    assert (
        SpanValue.record_kind == "typed-archive-object"
        and SpanValue.length == EndValue - OffsetValue
    )
    PlanesValue = tuple(
        ItemValue
        for ItemValue in Document.feature_timeline
        if ItemValue.name in ("Front Plane", "Top Plane", "Right Plane")
    )
    assert len(PlanesValue) == 3 and all(
        ItemValue.attributes["typed_archive_owner"] for ItemValue in PlanesValue
    )
