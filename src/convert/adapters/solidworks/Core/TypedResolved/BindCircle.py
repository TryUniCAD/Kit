from dataclasses import replace as ReplaceValue
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import (
    NativeProfile,
    NativeRule,
    NativeSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadCircleShape import (
    ReadCircleShape,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadRadialDrive import (
    ReadRadialDrive,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the fixed center must match one public marker and the actual native point relation
def ReadCircCenter(
    Sketch: NativeSketch,
    SketchValue: ArchiveNode,
    Profile: NativeProfile,
    CenterIndex: int,
) -> int | None:
    XValue, YValue, _ = Profile.coordinates
    Centers = [
        Index
        for Index, Marker in enumerate(Sketch.markers)
        if Marker.semantic == "point"
        and Marker.coordinates_mm is not None
        and IsClose(Marker.coordinates_mm[0], XValue, rel_tol=0.0, abs_tol=1e-8)
        and IsClose(Marker.coordinates_mm[1], YValue, rel_tol=0.0, abs_tol=1e-8)
    ]
    if len(Centers) != 1:
        return None
    DimFields = NativeRecord(SketchValue.FieldsValue.get("dims"))
    Relations = NativeRows(DimFields.get("log_g1"))
    if len(Relations) != 1 or any(
        DimFields.get(NameValue) for NameValue in ("log_g2", "log_g3")
    ):
        return None
    Relation = NativeRecord(Relations[0].get("d"))
    Handle = RequireNative(Relation.get("h1"), "sgPointHandle")
    if Relation.get("f80") != 17 or Handle.FieldsValue.get("idx") != CenterIndex:
        return None
    return Centers[0]


# the supported circle must preserve established public ids and bind both native constraint targets
def BindCircle(
    Sketch: NativeSketch, NodeValue: ArchiveNode, LinkValue: NativeLink
) -> NativeSketch | None:
    SeamMarkers = [
        Marker
        for Marker in Sketch.markers
        if Marker.semantic == "circle" and Marker.endpoint_indices is None
    ]
    CircleMarkers = [
        Marker
        for Marker in Sketch.markers
        if Marker.semantic in ("reference", "circle")
        and Marker.endpoint_indices is not None
        and Marker.endpoint_indices[0] == Marker.endpoint_indices[1]
    ]
    if (
        len(SeamMarkers) != 1
        or len(CircleMarkers) != 1
        or len(Sketch.dimensions) != 1
        or len(Sketch.profiles) > 1
        or any(Profile.kind != "circle" for Profile in Sketch.profiles)
    ):
        return None
    SketchValue = RequireNative(NodeValue.FieldsValue.get("pd_f80"), "sgSketch")
    Shape = ReadCircleShape(SketchValue)
    if Shape is None:
        return None
    Drive = ReadRadialDrive(LinkValue, SketchValue)
    if Drive is None:
        return None
    Profile, CenterIndex = Shape
    Dimension, KindValue, RadialNode = Drive
    StartValue, EndValue = RadialNode.StartOffset, RadialNode.EndOffset
    if (
        Sketch.dimensions[0].name != Dimension.name
        or StartValue is None
        or EndValue is None
        or EndValue <= StartValue
    ):
        return None
    ParameterKey = f"{Sketch.object_id}:{Dimension.name}"
    Rules = [
        RuleValue
        for RuleValue in Sketch.constraints
        if RuleValue.parameter == ParameterKey
    ]
    if len(Sketch.constraints) != 1 or len(Rules) != 1:
        return None
    CenterMarker = ReadCircCenter(Sketch, SketchValue, Profile, CenterIndex)
    if CenterMarker is None:
        return None
    RadialRule = ReplaceValue(
        Rules[0],
        kind=KindValue,
        references=(f"{Sketch.object_id}:profile:0",),
        value=Dimension.value_mm,
        native_code=3 if KindValue == "radius" else 15,
        native_offset=StartValue,
        native_length=EndValue - StartValue,
        reference_points=(),
    )
    FixedRule = NativeRule(
        f"{Sketch.object_id}:center:fixed",
        "fixed",
        (f"native-index:{CenterMarker}",),
        None,
        None,
        None,
        17,
    )
    Profile = ReplaceValue(
        Profile,
        parameter_name=Dimension.name,
        dimension_kind=KindValue,
        marker_offsets=(SeamMarkers[0].offset, CircleMarkers[0].offset),
        EntityMarkerOffset=None if Sketch.profiles else CircleMarkers[0].offset,
    )
    return ReplaceValue(
        Sketch,
        profiles=(Profile,),
        dimensions=(ReplaceValue(Dimension, kind=KindValue),),
        constraints=(RadialRule, FixedRule),
    )
