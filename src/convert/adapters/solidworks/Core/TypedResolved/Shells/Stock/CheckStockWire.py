from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the retained contour and region both reference the actual four stock segments
def CheckStockWire(
    ProfileNode: ArchiveNode, SketchNode: ArchiveNode, LoopValue: LineLoop
) -> None:
    CacheValue = NativeRecord(ProfileNode.FieldsValue.get("d5c0"))
    (ChainRow,) = NativeRows(CacheValue.get("f2a8"))
    Chain = RequireNative(ChainRow.get("chain"), "moSketchChain_c")
    Lines = NativeRecord(Chain.FieldsValue.get("f08"))
    ItemsValue = NativeRows(Lines.get("items"))
    if (
        CacheValue.get("f2b0") != 1
        or CacheValue.get("n2a8") != 1
        or Lines.get("n") != 4
        or len(ItemsValue) != 4
        or {RowValue.get("v") for RowValue in ItemsValue}
        != {Value.PermanentId for Value in LoopValue.LinesValue}
        or Chain.FieldsValue.get("fc0") is not None
        or Chain.FieldsValue.get("fc8") is not None
    ):
        raise ValueError("SOLIDWORKS stock contour does not own its actual four lines")
    RegionList = RequireNative(
        SketchNode.FieldsValue.get("f5d8"), "suObList"
    ).FieldsValue
    (RegionRow,) = NativeRows(RegionList.get("items"))
    RegionValue = RequireNative(RegionRow.get("o"), "moSketchRegion_c")
    UseList = RequireNative(RegionValue.FieldsValue.get("f08"), "suObList").FieldsValue
    UsesValue = NativeRows(UseList.get("items"))
    if (
        RegionList.get("n") != 1
        or UseList.get("n") != 4
        or len(UsesValue) != 4
        or {ReadDimHandle(UseValue.get("o"), "sgLineHandle") for UseValue in UsesValue}
        != {Value.IndexValue + 1 for Value in LoopValue.LinesValue}
    ):
        raise ValueError("SOLIDWORKS stock region does not alias its actual line ring")
