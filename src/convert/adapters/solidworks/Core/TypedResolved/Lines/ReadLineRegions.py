from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a cached single region may describe only the same complete active contour and must retain every actual boundary handle
def ReadLineRegions(
    SketchValue: ArchiveNode, LinesValue: tuple[LineSegment, ...], LinkValue: NativeLink
) -> tuple[Mapping[str, object], ...]:
    ListValue = RequireNative(SketchValue.FieldsValue.get("f5d8"), "suObList")
    Regions = NativeRows(ListValue.FieldsValue.get("items"))
    if ListValue.FieldsValue.get("n") != len(Regions) or len(Regions) > 1:
        raise ValueError("typed line ring has an unqualified region collection")
    ResultValues: list[Mapping[str, object]] = []
    for RowValue in Regions:
        RegionValue = RequireNative(RowValue.get("o"), "moSketchRegion_c")
        Boundary = RequireNative(RegionValue.FieldsValue.get("f08"), "suObList")
        Handles = tuple(
            RequireNative(BoundaryRow.get("o"), "sgLineHandle")
            for BoundaryRow in NativeRows(Boundary.FieldsValue.get("items"))
        )
        Indices = tuple(ReadDimHandle(Handle, "sgLineHandle") for Handle in Handles)
        if (
            Boundary.FieldsValue.get("n") != len(Handles)
            or len(Handles) != len(LinesValue)
            or len(set(Indices)) != len(Indices)
            or set(Indices) != {LineValue.IndexValue for LineValue in LinesValue}
        ):
            raise ValueError(
                "typed line region does not bind the complete actual active contour"
            )
        ResultValues.append(
            {
                "owner": NativeNodeSpan(LinkValue, RegionValue),
                "boundary_owner": NativeNodeSpan(LinkValue, Boundary),
                "native_line_indices": Indices,
                "handles": tuple(
                    {
                        "owner": NativeNodeSpan(LinkValue, Handle),
                        "fields": dict(Handle.FieldsValue),
                    }
                    for Handle in Handles
                ),
            }
        )
    return tuple(ResultValues)
