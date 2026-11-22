from convert.adapters.solidworks.Archive.Construction.Sketch.DimensionArrays import (
    KDimensionArrays,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.SketchArrays import (
    KSketchArrays,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimBase import (
    CheckDimBase,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the model origin cannot conceal additional sketch geometry or driving relations outside the reconstructed user contour
def CheckOriginGeom(OriginValue: ArchiveNode) -> None:
    Fields = RequireNative(
        OriginValue.FieldsValue.get("pd_f80"), "sgSketch"
    ).FieldsValue
    PointsValue = NativeRows(Fields.get("points"))
    if Fields.get("npoints") != 1 or len(PointsValue) != 1:
        raise ValueError(
            "cache free prism requires the single actual model origin point"
        )
    for CountName, FieldName in KSketchArrays:
        if FieldName != "points" and (
            Fields.get(CountName) != 0 or not IsLineState(Fields.get(FieldName))
        ):
            raise ValueError("cache free prism origin contains additional geometry")
    PointValue = NativeRecord(PointsValue[0].get("point"))
    if (
        PointsValue[0].get("kind") != 0
        or PointValue.get("f0c") != 1
        or NativeRecord(PointValue.get("pos")) != {"x": 0.0, "y": 0.0}
    ):
        raise ValueError("cache free prism origin point is displaced or external")
    Dimensions = NativeRecord(Fields.get("dims"))
    for CountName, FieldName in KDimensionArrays:
        if FieldName != "log_g1" and (
            Dimensions.get(CountName) != 0 or not IsLineState(Dimensions.get(FieldName))
        ):
            raise ValueError("cache free prism origin has extra dimensions")
    Relations = NativeRows(Dimensions.get("log_g1"))
    if Dimensions.get("nlog1") != 1 or len(Relations) != 1:
        raise ValueError("cache free prism origin has an unqualified fixed relation")
    Relation = NativeRecord(Relations[0].get("d"))
    CheckDimBase(Relation)
    if (
        Relation.get("f80") != 17
        or Relation.get("f28") is not None
        or Relation.get("fa0") != 0xFFFE
        or Relation.get("fa4") != 0
        or ReadDimHandle(Relation.get("h1"), "sgPointHandle") != 0
    ):
        raise ValueError(
            "cache free prism model origin is not fixed at its actual point"
        )
