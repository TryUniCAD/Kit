from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.CheckAxisMap import (
    CheckAxisMap,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadPrismAxes import (
    ReadPrismAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# additional datum roots can leave the equation inventory only after their complete linked ownership is proved
def ReadEqFeatures(
    LinkValue: NativeLink, SourceValue: SldprtArchive
) -> tuple[dict[int, ArchiveNode], bool]:
    Features = IndexFeatures(LinkValue)
    if not any(
        Value.ClassValue.NameValue == "moRefAxis_c" for Value in Features.values()
    ):
        return Features, False
    if (
        not IsCacheAbsent(SourceValue)
        or LinkValue.ResolvedValue.ExtraFields is not None
    ):
        raise ValueError("local equation with axes requires an exact cache-free part")
    HeaderValue = ReadHeaderGraph(SourceValue.require("Header2"), 19000)
    AxisValue = ReadPrismAxes(LinkValue, HeaderValue, Features)
    NodesValue = tuple(
        Entry.EntryValue
        for Entry in LinkValue.ResolvedValue.MapValue.EntriesValue
        if isinstance(Entry.EntryValue, ArchiveNode)
    )
    StockNodes, _ = CheckAxisMap(LinkValue, Features, NodesValue, AxisValue)
    return StockNodes, True
