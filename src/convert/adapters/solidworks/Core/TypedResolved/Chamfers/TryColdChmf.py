from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.BuildChmfGeom import (
    ChmfPrism,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.CheckChmfCold import (
    CheckChmfCold,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.CheckChmfView import (
    CheckChmfView,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.JoinChmfEdge import (
    JoinChmfEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import (
    ReadChmfOwn,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRoots import (
    ReadChmfRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    ReadChmfRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfStock import (
    ReadChmfStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# the complete cold part uses exact owned archive support and never falls back to inferred shape data
def ReadColdChmf(Archive: SldprtArchive, ModelValue: NativeModel) -> ChmfPartRead:
    LinkValue = ReadNativeLink(Archive, 0, ReadChamfers=True)
    Owners = ReadChmfOwn(LinkValue, ColdValue=True)
    CheckChmfCold(LinkValue, Owners)
    Roots, Nodes = ReadChmfRoots(LinkValue, ModelValue, Owners.FeatureValue)
    StockValue, PrismValue, LoopValue = ReadChmfStock(
        LinkValue, Owners.StockValue, Nodes
    )
    StockOp, ChmfOp = ModelValue.operations
    if (
        StockOp.object_id != NativeNodeId(Owners.StockValue)
        or ChmfOp.object_id != NativeNodeId(Owners.FeatureValue)
        or StockOp.profile_id != NativeNodeId(StockValue.ProfileValue)
        or ChmfOp.dependencies != (StockOp.object_id,)
    ):
        raise ValueError(
            "cold chamfer differs from its actual preceding public stock and operation"
        )
    Header = ReadHeaderGraph(Archive.require("Header2"), 19000)
    Roles = ReadChmfRows(LinkValue, Owners, Header)
    EdgeValue = JoinChmfEdge(PrismValue, LoopValue, Roles)
    PartValue = ChmfPartRead(
        LinkValue,
        Owners,
        StockValue,
        ChmfPrism(LinkValue, Owners, EdgeValue),
        EdgeValue,
        Roots,
    )
    CheckChmfView(PartValue)
    return PartValue


# exact cold chamfers opt into the typed link only after their ordinary source profile is witnessed
def TryColdChmf(
    Archive: SldprtArchive,
    ModelValue: NativeModel,
    Settings: ReadOptions,
) -> ChmfPartRead | None:
    if (
        Settings.extract_raw_brep
        or ModelValue.active_configuration_id != 0
        or tuple(
            (Value.configuration_id, Value.name) for Value in ModelValue.configurations
        )
        != ((0, "Default"),)
        or tuple(Value.kind for Value in ModelValue.operations) != ("join", "chamfer")
        or len(ModelValue.sketches) != 1
        or not IsCacheAbsent(Archive)
    ):
        return None
    try:
        return ReadColdChmf(Archive, ModelValue)
    except (ValueError, TypeError, KeyError, OverflowError):
        return None
