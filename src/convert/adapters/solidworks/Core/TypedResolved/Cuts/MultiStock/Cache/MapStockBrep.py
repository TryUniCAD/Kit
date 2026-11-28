from collections import Counter
from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.Geometry.Parasolid import NativeId
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadBrepGroups import (
    ReadBrepGroups,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheFaces import (
    ReadCacheFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheBody import (
    StockCacheBody,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepBody


# the legacy surface model may keep exact geometry while collapsing physical body membership
def MapStockBrep(
    NodesValue: Mapping[int, XmtNode],
    ModelValue: BrepModel,
    BodyValues: tuple[StockCacheBody, StockCacheBody],
) -> BrepModel:
    Groups = ReadBrepGroups(ModelValue)
    Carriers = {FaceValue.id: FaceValue.surface_id for FaceValue in ModelValue.faces}
    NodeCounts = Counter(NodeValue.KindValue for NodeValue in NodesValue.values())
    if (
        NodeCounts[13] != 4
        or NodeCounts[19] != 4
        or set(Carriers) != {
            NativeId("face", NodeValue.IndexValue + 1)
            for NodeValue in NodesValue.values()
            if NodeValue.KindValue == 14
        }
    ):
        raise ValueError("saved stock cache has unowned native faces or shell topology")
    Bodies: list[BrepBody] = []
    for BodyValue in BodyValues:
        Faces = ReadCacheFaces(NodesValue, BodyValue.KernelValue)
        Region = Groups.pop(frozenset(Faces), None)
        if Region is None or any(
            Carriers.pop(FaceId, None) != SurfaceId for FaceId, SurfaceId in Faces.items()
        ):
            raise ValueError("saved stock body does not match its decoded faces and carriers")
        Bodies.append(
            BrepBody(
                f"sldprt:brep:body:atom:{BodyValue.AtomId}",
                (Region,),
                design_body_id=BodyValue.DesignId,
            )
        )
    if Carriers or Groups:
        raise ValueError("saved stock body projection leaves unowned decoded geometry")
    Result = ReplaceValue(ModelValue, bodies=tuple(Bodies))
    if Result.validate(frozenset(BodyValue.DesignId for BodyValue in BodyValues)):
        raise ValueError("saved stock body projection violates actual topology ownership")
    return Result
