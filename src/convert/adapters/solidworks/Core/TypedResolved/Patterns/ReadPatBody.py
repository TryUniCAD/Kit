from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBrepOwners import (
    CheckBrepOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheBody import (
    ReadCacheBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheFaces import (
    ReadCacheFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockData import (
    ReadStockData,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheBody import (
    StockCacheBody,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from interchange.document.Models.DocumentModel import CadDocument


# the original physical body remains authoritative only after its world atom and full face set agree
def ReadPatBody(
    Document: CadDocument,
    Archive: SldprtArchive,
    LinkValue: NativeLink,
    OwnerValue: PatternOwner,
) -> StockCacheBody:
    NodesValue, Geometry = ReadStockData(Archive, LinkValue.ConfigName + "-Partition")
    if (
        len(Document.bodies) != 1
        or Document.brep != Geometry
        or len(Geometry.regions) != 1
    ):
        raise ValueError("pattern requires the actual selected single solid partition")
    CheckBrepOwners(Geometry, Document.bodies[0].id)
    WorldValue = RequireXmt(NodesValue, 1, 101)
    BodyIds = WalkXmtChain(
        NodesValue, WorldValue.Integer("body"), 12, OwnerField="owner", OwnerValue=1
    )
    if len(BodyIds) != 1 or set(BodyIds) != {
        Value.IndexValue for Value in NodesValue.values() if Value.KindValue == 12
    }:
        raise ValueError("pattern world has detached or additional physical bodies")
    BodyValue = NodesValue[BodyIds[0]]
    Faces = ReadCacheFaces(NodesValue, BodyValue)
    if len(Faces) != 6 + 5 * OwnerValue.DriversValue[0].LiveValue or Faces != {
        Value.id: Value.surface_id for Value in Geometry.faces
    }:
        raise ValueError(
            "pattern physical body does not own every neutral face and carrier"
        )
    return ReadCacheBody(
        NodesValue,
        BodyValue,
        {OwnerValue.AtomsValue[-1]: (OwnerValue.OutputValue, OwnerValue.NodeValue)},
    )
