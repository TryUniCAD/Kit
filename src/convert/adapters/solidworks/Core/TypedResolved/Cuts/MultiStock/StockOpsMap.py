from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
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
    Model: NativeModel,
    NodesValue: Mapping[int, ArchiveNode],
    Lineage: StockCutLineage | ColdStockOwners,
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
    SelectedIndex = (
        Lineage.SelectedIndex
        if isinstance(Lineage, ColdStockOwners)
        else Lineage.AtomsValue.SelectedIndex
    )
    Selected = StockValues[SelectedIndex].NodeValue
    Untouched = StockValues[1 - SelectedIndex].NodeValue
    CutId = NativeNodeId(CutValue.NodeValue)
    OwnersValue[CutId] = ReplaceValue(
        CutValue, ParentsValue=(Selected, CutValue.ProfileValue)
    )
    if isinstance(Lineage, ColdStockOwners):
        return OwnersValue, {
            "binding": "cold_two_stock_explicit_wrapper",
            "feature_scope_code": 1,
            "producer_feature_id": NativeNodeId(Selected),
            "untouched_producer_feature_id": NativeNodeId(Untouched),
            "consumer_feature_id": CutId,
            "selected_stock_atom_id": Lineage.SelectedAtomId,
            "untouched_stock_atom_id": ReadCutAtomId(
                Lineage.StockAtoms[1 - SelectedIndex], Untouched
            ),
        }
    AtomsValue = Lineage.AtomsValue
    MergeTolerance = StockValues[1].NodeValue.FieldsValue.get("f838")
    return OwnersValue, {
        "binding": "saved_two_stock_atom_alias",
        "feature_scope_code": 1,
        "producer_feature_id": NativeNodeId(Selected),
        "untouched_producer_feature_id": NativeNodeId(Untouched),
        "consumer_feature_id": CutId,
        "consumed_atom_id": ReadCutAtomId(AtomsValue.ConsumedAtom, Selected),
        "untouched_atom_id": ReadCutAtomId(AtomsValue.UntouchedAtom, Untouched),
        "result_atom_id": ReadCutAtomId(AtomsValue.ResultAtom, CutValue.NodeValue),
        **(
            {"native_independent_stock_merge_tolerance_m": MergeTolerance}
            if MergeTolerance
            else {}
        ),
    }
