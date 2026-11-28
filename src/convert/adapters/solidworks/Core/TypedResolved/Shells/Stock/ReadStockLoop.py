from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.SavedScope.CheckSavedChain import (
    CheckSavedChain,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineOrder import LineOrder
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLinePoint import (
    ReadLinePoint,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLiveLines import (
    ReadLiveLines,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineRegions import (
    ReadLineRegions,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Shells.Stock.CheckStockRels import (
    CheckStockRels,
    ReadStockRels,
)


# the native rectangle starts its operative line rows after an unreferenced construction cell
def ReadStockLoop(ProfileValue: ArchiveNode, LinkValue: NativeLink) -> LineLoop:
    SketchNode = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    Fields = SketchNode.FieldsValue
    CheckLineScope(Fields, HasDrivers=True, HasRegions=True)
    PointRows = NativeRows(Fields.get("points"))
    LineRows = NativeRows(Fields.get("lines"))
    if (Fields.get("npoints"), Fields.get("nlines"), len(PointRows), len(LineRows)) != (
        4,
        5,
        4,
        5,
    ):
        raise ValueError(
            "SOLIDWORKS shell stock is outside the saved rectangle profile"
        )
    LeadValue = NativeRecord(LineRows[0].get("line"))
    if (
        any(
            LeadValue.get(NameValue) != Value
            for NameValue, Value in {
                "f08": 0,
                "f0c": -1,
                "f20": 0,
                "f54": 5,
                "fd0": 0,
                "fd4": 0,
                "ext": None,
                "group": None,
            }.items()
        )
        or LineRows[0].get("flags") != 0
    ):
        raise ValueError("SOLIDWORKS shell stock has another initial sketch cell")
    Points = {
        IndexValue: ReadLinePoint(RowValue, IndexValue)
        for IndexValue, RowValue in enumerate(PointRows)
    }
    Relations = ReadStockRels(Fields)
    Lines, RetiredRows = ReadLiveLines(
        LineRows, {("line", IndexValue): 1 for IndexValue in Relations}
    )
    Regions = ReadLineRegions(SketchNode, Lines, LinkValue)
    if (
        any(Value.CreationId <= 0 for Value in Points.values())
        or len(Lines) != 4
        or len(RetiredRows) != 1
        or len(Regions) != 1
    ):
        raise ValueError("SOLIDWORKS saved shell stock lost its closed line region")
    LoopValue = LineLoop(
        Points,
        Lines,
        LineOrder(Points, Lines),
        NativeNodeSpan(LinkValue, SketchNode),
        RetiredRows=RetiredRows,
        RegionValues=Regions,
    )
    CheckStockRels(Relations, LoopValue)
    CheckSavedChain(LinkValue, ProfileValue.FieldsValue.get("d5c0"), LoopValue)
    return LoopValue
