from math import pi as PiValue

from convert.adapters.solidworks.Core.Native import KRefSupportSource
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwProfile import (
    SwReadProfile,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ValueKind
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter, ParameterValue


# recovered sketch dimensions remain distinct live parameters rather than rounded display values
def MakeSwLength(
    LinkValue: NativeLink, ProfileValue: SwReadProfile, SketchId: str
) -> Parameter:
    Driver = ProfileValue.DriverValue
    ParamId = f"sldprt:dimension:{Driver.NativeId}"
    OwnerValue = NativeNodeSpan(LinkValue, Driver.ParameterValue)
    return Parameter(
        ParamId,
        "D1",
        ParameterValue(Driver.MetresValue * 1000.0, ValueKind.KLength, "mm"),
        owner_id=SketchId,
        provenance=TypedProvenance(OwnerValue, str(Driver.NativeId)),
        attributes={
            "typed_archive_owner": dict(OwnerValue)
            | {
                "value_field": "f58",
                "dimension_id": Driver.NativeId,
                "dimension_index": Driver.DimensionValue.IndexValue,
            }
        },
    )


# only the already verified exact point relations are projected from the native sketch
def MakeSwRules(
    EntityId: str, ParamId: str, IsSection: bool
) -> tuple[SketchRelation, ...]:
    Center = ConstraintRef(EntityId, "center")
    Start = ConstraintRef(EntityId, "start")
    EndPoint = ConstraintRef(EntityId, "end")
    if IsSection:
        return (
            SketchRelation(f"{EntityId}:fixed", "fixed", (Center,)),
            SketchRelation(
                f"{EntityId}:diameter", "diameter", (ConstraintRef(EntityId),), ParamId
            ),
        )
    return (
        SketchRelation(f"{EntityId}:fixed", "fixed", (Start,)),
        SketchRelation(f"{EntityId}:vertical", "vertical", (Center, Start)),
        SketchRelation(f"{EntityId}:horizontal", "horizontal", (EndPoint, Center)),
        SketchRelation(
            f"{EntityId}:radius", "radius", (ConstraintRef(EntityId),), ParamId
        ),
    )


# canonical millimetre sketch stores the recovered section and path with stable native owner identifiers
def MakeSwSketch(
    LinkValue: NativeLink, ProfileValue: SwReadProfile
) -> tuple[Sketch, Parameter]:
    FeatureValue = ProfileValue.FeatureValue
    NativeId = NativeNodeId(FeatureValue)
    SketchId = f"sldprt:sketch:{NativeId}"
    EntityId = f"{SketchId}:arc:0"
    ParamValue = MakeSwLength(LinkValue, ProfileValue, SketchId)
    SectionValue = isinstance(ProfileValue.CurveValue, CircleGeometry)
    RadiusValue = ProfileValue.CurveValue.Radius * 1000.0
    GeometryValue = (
        CircleGeometry(PlaneVector(0.0, 0.0), RadiusValue)
        if SectionValue
        else ArcGeometry(
            PlaneVector(0.0, RadiusValue), RadiusValue, -PiValue / 2.0, 0.0
        )
    )
    EntityValue = SketchEntity(
        EntityId,
        GeometryKind.KCircle if SectionValue else GeometryKind.KArcGeometry,
        GeometryValue,
        attributes=SwSeamAttrs(ProfileValue),
    )
    return (
        Sketch(
            SketchId,
            ReadNativeName(FeatureValue),
            f"sldprt:plane:{ProfileValue.DatumId}",
            (EntityValue,),
            MakeSwRules(EntityId, ParamValue.id, SectionValue),
            (ParamValue.id,),
            ((EntityValue.id,),) if SectionValue else (),
            provenance=TypedProvenance(
                NativeNodeSpan(LinkValue, FeatureValue), str(NativeId)
            ),
            attributes={
                "support_plane_source": KRefSupportSource,
                "support_plane_native_id": ProfileValue.DatumId,
            },
        ),
        ParamValue,
    )


# the sketch circle keeps its exact shared millimetre point through neutral serialization
def SwSeamAttrs(ProfileValue: SwReadProfile) -> dict[str, object]:
    SeamValue = ProfileValue.SeamValue
    if SeamValue is None:
        return {}
    return {
        "periodic_seam": {
            "point_mm": (
                SeamValue.PointValue.x * 1000.0,
                SeamValue.PointValue.y * 1000.0,
            ),
            "center_index": SeamValue.CenterIndex,
            "start_end_index": SeamValue.SeamIndex,
            "point_marks": SeamValue.MarkValues,
        }
    }
