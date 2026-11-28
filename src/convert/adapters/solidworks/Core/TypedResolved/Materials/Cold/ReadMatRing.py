from math import inf as Infinity, nextafter as NextFloat

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDriver import (
    ReadLineDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter, ParameterValue


# the portable coordinate must project back to the original binary metre ordinate
def ReadMatMm(Metres: float) -> float:
    Millimetres = Metres / 0.001
    for Value in (
        Millimetres,
        NextFloat(Millimetres, Infinity),
        NextFloat(Millimetres, -Infinity),
    ):
        if Value * 0.001 == Metres:
            return Value
    raise ValueError(
        "cold rectangle point does not have an exact millimetre projection"
    )


# the origin constraint group selects actual local and external points independent of contour position
def ReadMatAnchor(SketchValue: ArchiveNode) -> str:
    Fields = SketchValue.FieldsValue
    DimFields = NativeRecord(Fields.get("dims"))
    Relations = ReadDimRows(DimFields, "nlog2", "log_g2")
    Points = NativeRows(Fields.get("points"))
    Lines = NativeRows(Fields.get("lines"))
    CountsValue = (len(Points), len(Lines), len(Relations))
    if CountsValue == (5, 4, 1):
        KindValue, LocalIndex = "corner", 0
    elif CountsValue == (6, 6, 3):
        KindValue, LocalIndex = "center", 4
    else:
        raise ValueError("cold rectangle lacks an owned corner or center relation")
    RelationValue = NativeRecord(Relations[-1].get("d"))
    if (
        RelationValue.get("f80") != 9
        or ReadDimHandle(RelationValue.get("h1"), "sgPointHandle") != len(Points) - 1
        or ReadDimHandle(RelationValue.get("h2"), "sgPointHandle") != LocalIndex
        or Points[-1].get("kind") != 1
    ):
        raise ValueError(
            "cold rectangle origin relation does not select its actual points"
        )
    return KindValue


# the first four point owners determine the model contour in the original local frame
def ReadMatPoints(SketchValue: ArchiveNode) -> tuple[PlaneVector, ...]:
    Positions: list[PlaneVector] = []
    for RowValue in NativeRows(SketchValue.FieldsValue.get("points"))[:4]:
        if RowValue.get("kind") != 0:
            raise ValueError("cold rectangle has a foreign contour point")
        PointValue = NativeRecord(RowValue.get("point"))
        Position = NativeRecord(PointValue.get("pos"))
        Positions.append(
            PlaneVector(
                ReadMatMm(RequireScalar(Position.get("x"))),
                ReadMatMm(RequireScalar(Position.get("y"))),
            )
        )
    return tuple(Positions)


# the live driver objects supply their own names values and point references
def ReadMatDrives(
    SketchValue: ArchiveNode, LinkValue: NativeLink, SketchId: str
) -> tuple[Parameter, ...]:
    DimFields = NativeRecord(SketchValue.FieldsValue.get("dims"))
    Values = ReadDimRows(DimFields, "ng2", "val_g2")
    Displays = RequireNative(DimFields.get("f118"), "suObList")
    Items = NativeRows(Displays.FieldsValue.get("items"))
    if len(Values) != 2 or len(Items) != 2:
        raise ValueError("cold rectangle requires two live sketch drivers")
    Drivers = tuple(
        ReadLineDriver(
            RowValue,
            IndexValue,
            RequireNative(DisplayValue.get("o"), "moDisplayDistanceDim_c"),
            SketchValue,
            LinkValue,
        )
        for IndexValue, (RowValue, DisplayValue) in enumerate(
            zip(Values, Items, strict=True)
        )
    )
    if tuple(Driver.PointValues for Driver in Drivers) != ((0, 1), (1, 2)):
        raise ValueError(
            "cold rectangle drivers must select the ordered width and height"
        )
    return tuple(
        Parameter(
            f"{SketchId}/length/{Driver.IndexValue}",
            Driver.NameValue,
            ParameterValue(Driver.MetresValue, ValueKind.KLength, "m"),
            ParameterRole.KDriving,
            owner_id=SketchId,
        )
        for Driver in Drivers
    )


# canonical contour relations remain attached to the same ordered editable edges
def MakeMatRules(
    EdgesValue: tuple[SketchEntity, ...], Drivers: tuple[Parameter, ...], SketchId: str
) -> tuple[SketchRelation, ...]:
    AxisRules = tuple(
        SketchRelation(
            f"{SketchId}/axis/{IndexValue}",
            "vertical" if IndexValue % 2 else "horizontal",
            (ConstraintRef(EdgeValue.id),),
        )
        for IndexValue, EdgeValue in enumerate(EdgesValue)
    )
    Lengths = tuple(
        SketchRelation(
            f"{Driver.id}/relation",
            "distance",
            (ConstraintRef(EdgeValue.id, "start"), ConstraintRef(EdgeValue.id, "end")),
            Driver.id,
        )
        for EdgeValue, Driver in zip(EdgesValue[:2], Drivers, strict=True)
    )
    return (*AxisRules, *Lengths)


# the canonical projection is checked by reproducing the complete archive before it can be exposed
def ReadMatRing(
    ProfileValue: ArchiveNode, LinkValue: NativeLink, PlaneId: str
) -> tuple[Sketch, tuple[Parameter, ...], str]:
    SketchNode = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    KindValue = ReadMatAnchor(SketchNode)
    Points = ReadMatPoints(SketchNode)
    SketchId = f"sldprt:sketch:{NativeNodeId(ProfileValue)}"
    Drivers = ReadMatDrives(SketchNode, LinkValue, SketchId)
    Edges = tuple(
        SketchEntity(
            f"{SketchId}/edge/{IndexValue}",
            GeometryKind.KLine,
            LineGeometry(PointValue, Points[(IndexValue + 1) % 4]),
        )
        for IndexValue, PointValue in enumerate(Points)
    )
    return (
        Sketch(
            SketchId,
            ReadNativeName(ProfileValue),
            PlaneId,
            Edges,
            MakeMatRules(Edges, Drivers, SketchId),
            parameter_ids=tuple(Value.id for Value in Drivers),
            closed_profile_entity_ids=(tuple(Value.id for Value in Edges),),
        ),
        Drivers,
        KindValue,
    )
