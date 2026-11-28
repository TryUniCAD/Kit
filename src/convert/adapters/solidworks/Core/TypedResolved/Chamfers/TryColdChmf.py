from dataclasses import replace as ReplaceValue

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeFeature, NativeModel
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
    if not IsCacheAbsent(Archive):
        raise ValueError("cold chamfer cannot own a saved body cache")
    LinkValue = ReadNativeLink(Archive, 0, ReadChamfers=True)
    Owners = ReadChmfOwn(LinkValue)
    CheckChmfCold(LinkValue, Owners)
    Roots, Nodes = ReadChmfRoots(LinkValue, ModelValue, Owners.FeatureValue)
    StockValue, PrismValue, LoopValue = ReadChmfStock(
        LinkValue, Owners.StockValue, Nodes
    )
    StockOp, ChmfOp = ModelValue.operations
    Feature = next(
        (Value for Value in ModelValue.features if Value.object_id == ChmfOp.object_id),
        None,
    )
    if (
        StockOp.object_id != NativeNodeId(Owners.StockValue)
        or ChmfOp.object_id != NativeNodeId(Owners.FeatureValue)
        or StockOp.profile_id != NativeNodeId(StockValue.ProfileValue)
        or ChmfOp.dependencies != (StockOp.object_id,)
        or Feature is None
        or tuple(Value.name for Value in Feature.dimensions)
        != tuple(Driver.NameValue for Driver in Owners.DriversValue)
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


# ordinary inspection reports unresolved current chamfer history without assigning it a portable definition
KChmfRejected = "SOLIDWORKS 2026 chamfer history requires the verified cold stock, selected edge and live drivers"


# native class names and explicit keyword kinds must still flag a chamfer when the operation could not be decoded
def IsChmfFeature(FeatureValue: NativeFeature) -> bool:
    return (
        FeatureValue.class_name in ("Chamfer_c", "moChamfer_c")
        or FeatureValue.kind.casefold().strip() == "chamfer"
    )


# raw extraction keeps its original payload lane while strict semantic reads reject unqualified current chamfers
def TryColdChmf(
    Archive: SldprtArchive,
    ModelValue: NativeModel,
    Settings: ReadOptions,
) -> tuple[NativeModel, ChmfPartRead | None]:
    if (
        Settings.extract_raw_brep
        or Archive.format_version != 4
        or not (
            any(Value.kind == "chamfer" for Value in ModelValue.operations)
            or any(IsChmfFeature(Value) for Value in ModelValue.features)
        )
        or ContainerMo(Archive.streams) != 19000
    ):
        return ModelValue, None
    try:
        if (
            ModelValue.active_configuration_id != 0
            or tuple(
                (Value.configuration_id, Value.name)
                for Value in ModelValue.configurations
            )
            != ((0, "Default"),)
            or tuple(Value.kind for Value in ModelValue.operations)
            != ("join", "chamfer")
            or len(ModelValue.sketches) != 1
        ):
            raise ValueError(
                "chamfer lacks its ordinary active configuration and preceding stock"
            )
        return ModelValue, ReadColdChmf(Archive, ModelValue)
    except (ValueError, TypeError, KeyError, OverflowError) as ErrorInfo:
        if Settings.strict:
            raise SldprtFormat(KChmfRejected) from ErrorInfo
        return (
            ReplaceValue(
                ModelValue, diagnostics=(*ModelValue.diagnostics, KChmfRejected)
            ),
            None,
        )
