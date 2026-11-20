from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import (
    StockCutLineage,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# selected dependencies must belong to this projection graph and precede the through cut
def StockOpsMap(
    Model: NativeModel, NodesValue: Mapping[int, ArchiveNode], Lineage: StockCutLineage
) -> tuple[dict[int, ExtrudeOwner], dict[str, object]]:
    StockValues = Lineage.StockValues
    CutValue = Lineage.CutValue
    OwnersValue = {
        NativeNodeId(OwnerValue.NodeValue): OwnerValue
        for OwnerValue in (*StockValues, CutValue)
    }
    if (
        len(OwnersValue) != 3
        or tuple(Operation.object_id for Operation in Model.operations)
        != tuple(OwnersValue)
        or tuple(Operation.kind for Operation in Model.operations)
        != ("join", "join", "cut")
        or any(
            NodesValue.get(OwnerId) is not OwnerValue.NodeValue
            for OwnerId, OwnerValue in OwnersValue.items()
        )
    ):
        raise ValueError(
            "selected two stock timeline differs from its linked producers"
        )
    AtomsValue = Lineage.AtomsValue
    Selected = StockValues[AtomsValue.SelectedIndex].NodeValue
    Untouched = StockValues[1 - AtomsValue.SelectedIndex].NodeValue
    CutId = NativeNodeId(CutValue.NodeValue)
    OwnersValue[CutId] = ReplaceValue(
        CutValue, ParentsValue=(Selected, CutValue.ProfileValue)
    )
    return OwnersValue, {
        "binding": "saved_two_stock_atom_alias",
        "feature_scope_code": 1,
        "producer_feature_id": NativeNodeId(Selected),
        "untouched_producer_feature_id": NativeNodeId(Untouched),
        "consumer_feature_id": CutId,
        "consumed_atom_id": ReadCutAtomId(AtomsValue.ConsumedAtom, Selected),
        "untouched_atom_id": ReadCutAtomId(AtomsValue.UntouchedAtom, Untouched),
        "result_atom_id": ReadCutAtomId(AtomsValue.ResultAtom, CutValue.NodeValue),
    }
