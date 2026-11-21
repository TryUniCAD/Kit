from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckBinaryDim import (
    CheckBinaryDim,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.LineOrigin import (
    LineOrigin,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.ReadOriginPoint import (
    ReadOriginPoint,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.ReadOriginRef import (
    ReadOriginRef,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# an origin group must preserve its real reference chain and exact point array roles before line geometry can be projected
def ReadOriginDim(SketchValue: ArchiveNode, LinkValue: NativeLink) -> LineOrigin | None:
    FieldsValue = NativeRecord(SketchValue.FieldsValue.get("dims"))
    RowsValue = ReadDimRows(FieldsValue, "nlog2", "log_g2")
    if not RowsValue:
        return None
    Points = NativeRows(SketchValue.FieldsValue.get("points"))
    Profiles = tuple(
        NodeValue
        for NodeValue in LinkValue.ResolvedValue.RootsValue
        if NodeValue is not None
        and NodeValue.ClassValue.NameValue == "moProfileFeature_c"
        and NodeValue.FieldsValue.get("pd_f80") is SketchValue
    )
    if len(RowsValue) != 1 or len(Points) != 5 or len(Profiles) != 1:
        raise ValueError(
            "typed origin group requires one actual corner profile and external point"
        )
    RelationValue = NativeRecord(RowsValue[0].get("d"))
    CheckBinaryDim(RelationValue, 9)
    ExternalIndex = ReadDimHandle(RelationValue.get("h1"), "sgPointHandle")
    LocalIndex = ReadDimHandle(RelationValue.get("h2"), "sgPointHandle")
    if (
        ExternalIndex != 4
        or LocalIndex != 0
        or any(RowValue.get("kind") != 0 for RowValue in Points[:4])
    ):
        raise ValueError(
            "typed origin relation does not bind the separate external row and first corner"
        )
    PointFields, ExternalValue, CreationId, PositionValue = ReadOriginPoint(
        Points[ExternalIndex]
    )
    OriginValue, Selection, Wrapper, Backup = ReadOriginRef(
        ExternalValue, Profiles[0], LinkValue
    )
    return LineOrigin(
        ExternalIndex,
        LocalIndex,
        CreationId,
        PositionValue,
        PointFields,
        RelationValue,
        OriginValue,
        Selection,
        Wrapper,
        ExternalValue,
        Backup,
        {
            **NativeNodeSpan(LinkValue, SketchValue),
            "embedded_array": "dims.log_g2",
            "row_index": 0,
            "embedded_class": "sgLogG2Dim",
        },
        {
            NameValue: NativeNodeSpan(LinkValue, NodeValue)
            for NameValue, NodeValue in (
                ("origin", OriginValue),
                ("selection", Selection),
                ("component", ArchiveNode.RequireNode(Selection.FieldsValue["f58"])),
                (
                    "point_handle",
                    ArchiveNode.RequireNode(Selection.FieldsValue["f0f8"]),
                ),
                ("wrapper", Wrapper),
                ("external", ExternalValue),
                ("backup", Backup),
            )
        },
    )
