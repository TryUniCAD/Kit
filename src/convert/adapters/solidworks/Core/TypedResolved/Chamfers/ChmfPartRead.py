from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfOwners import (
    ChmfOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector


# a uniquely resolved finite edge ties neutral witnesses to its preceding physical stock
@DataClass(frozen=True, slots=True)
class ChmfEdgeRead:
    EdgePoint: SpaceVector
    FacePoint: SpaceVector
    EdgeAxis: int
    DistanceAxis: int
    CornerBits: tuple[int, int, int]
    BoundsValue: BoundingBox


# cold semantics and derived shape retain one exact linked graph and its actual feature owners
@DataClass(frozen=True, slots=True)
class ChmfPartRead:
    LinkValue: NativeLink
    OwnersValue: ChmfOwners
    StockValue: ExtrudeOwner
    PrismValue: PrismPlan
    EdgeValue: ChmfEdgeRead
    RootsValue: tuple[ArchiveNode, ...]
