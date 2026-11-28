from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimBase import (
    CheckDimBase,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the selected point must belong to the actual origin sketch and its own retained fixed point relation
def CheckOriginNode(OriginValue: ArchiveNode, SelectionValue: ArchiveNode) -> None:
    SketchValue = RequireNative(OriginValue.FieldsValue.get("pd_f80"), "sgSketch")
    RowsValue = NativeRows(SketchValue.FieldsValue.get("points"))
    if len(RowsValue) != 1 or SketchValue.FieldsValue.get("npoints") != 1:
        raise ValueError("typed model origin requires its single actual point")
    PointValue = NativeRecord(RowsValue[0].get("point"))
    PositionValue = NativeRecord(PointValue.get("pos"))
    if (
        PointValue.get("f08") != PointValue.get("f0c")
        or PointValue.get("f0c") != 1
        or SelectionValue.FieldsValue.get("f100") != PointValue.get("f08")
        or PositionValue.get("x") != 0.0
        or PositionValue.get("y") != 0.0
        or ReadDimHandle(SelectionValue.FieldsValue.get("f0f8"), "sgPointHandle") != 0
    ):
        raise ValueError("typed origin selection does not bind its actual point")
    Dimensions = NativeRecord(SketchValue.FieldsValue.get("dims"))
    Relations = ReadDimRows(Dimensions, "nlog1", "log_g1")
    if len(Relations) != 1:
        raise ValueError("typed model origin lacks its owned fixed relation")
    RelationValue = NativeRecord(Relations[0].get("d"))
    CheckDimBase(RelationValue)
    if (
        RelationValue.get("f80") != 17
        or RelationValue.get("f28") is not None
        or RelationValue.get("fa0") != 0xFFFE
        or RelationValue.get("fa4") != 0
        or ReadDimHandle(RelationValue.get("h1"), "sgPointHandle") != 0
    ):
        raise ValueError("typed model origin is not fixed at its actual local point")
