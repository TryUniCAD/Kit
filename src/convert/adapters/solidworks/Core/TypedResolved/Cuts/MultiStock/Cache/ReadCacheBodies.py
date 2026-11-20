from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheBody import (
    ReadCacheBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheBody import (
    StockCacheBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import (
    StockCutLineage,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)


# the world must own exactly the two surviving atoms without depending on body order
def ReadCacheBodies(
    NodesValue: Mapping[int, XmtNode], Lineage: StockCutLineage
) -> tuple[StockCacheBody, StockCacheBody]:
    AtomsValue = Lineage.AtomsValue
    Untouched = Lineage.StockValues[1 - AtomsValue.SelectedIndex].NodeValue
    Producer = Lineage.CutValue.NodeValue
    UntouchedId = ReadCutAtomId(AtomsValue.UntouchedAtom, Untouched)
    ResultId = ReadCutAtomId(AtomsValue.ResultAtom, Producer)
    Owners = {
        UntouchedId: (AtomsValue.UntouchedAtom, Untouched),
        ResultId: (AtomsValue.ResultAtom, Producer),
    }
    World = RequireXmt(NodesValue, 1, 101)
    Definitions = WalkXmtChain(
        NodesValue, World.Integer("attrib_def"), 80, PreviousField=None
    )
    if set(Definitions) != {
        NodeValue.IndexValue for NodeValue in NodesValue.values() if NodeValue.KindValue == 80
    }:
        raise ValueError("saved stock cache has unregistered attribute definitions")
    Bodies = WalkXmtChain(
        NodesValue, World.Integer("body"), 12, OwnerField="owner", OwnerValue=1
    )
    if len(Bodies) != 2 or set(Bodies) != {
        NodeValue.IndexValue for NodeValue in NodesValue.values() if NodeValue.KindValue == 12
    }:
        raise ValueError("saved stock cache has detached or alternate world bodies")
    Bound = {
        BodyValue.AtomId: BodyValue
        for BodyValue in (
            ReadCacheBody(NodesValue, NodesValue[BodyIndex], Owners)
            for BodyIndex in Bodies
        )
    }
    if set(Bound) != set(Owners) or len(Owners) != 2:
        raise ValueError("saved kernel bodies do not bijectively identify the surviving atoms")
    return Bound[UntouchedId], Bound[ResultId]
