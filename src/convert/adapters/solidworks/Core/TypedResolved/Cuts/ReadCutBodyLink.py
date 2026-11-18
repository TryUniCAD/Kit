from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckColdPocket import (
    CheckColdPocket,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import (
    CheckSavedCutScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadColdSelectedStock import (
    ReadColdSelectedStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import (
    ReadManagedCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSavedCutBodies import (
    ReadSavedCutBodies,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.Features.FeatureExtrude import ExtrudeEnd


# saved pointer evidence and cold intersection evidence must retain their distinct provenance
def ReadCutBodyLink(
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    BossValue: ExtrudeOwner,
    CutValue: ExtrudeOwner,
) -> dict[str, object]:
    ManagedValues = ReadManagedCutAtoms(LinkValue)
    BodyEvidence: dict[str, object] = {
        "producer_feature_id": NativeNodeId(BossValue.NodeValue),
        "consumer_feature_id": NativeNodeId(CutValue.NodeValue),
    }
    if not ManagedValues:
        CheckColdPocket(LinkValue, Features, BossValue, CutValue)
        return {
            **BodyEvidence,
            "binding": "cold_all_bodies_intersection",
            "feature_scope_code": 0,
        }
    if len(ManagedValues) == 1 and CutValue.ModeValue == ExtrudeEnd.KThroughAll:
        StockAtom, AtomId = ReadColdSelectedStock(
            LinkValue, BossValue.NodeValue, CutValue.NodeValue
        )
        CheckColdPocket(LinkValue, Features, BossValue, CutValue, StockAtom)
        return {
            **BodyEvidence,
            "binding": "cold_selected_stock_atom",
            "consumed_atom_id": AtomId,
            "feature_scope_code": 1,
        }
    BossAtom, CutAtom = ReadSavedCutBodies(
        BossValue.NodeValue, CutValue.NodeValue, ManagedValues
    )
    ScopeValue = CheckSavedCutScope(
        LinkValue.ConfigValue.RootValue,
        BossValue.NodeValue,
        CutValue.NodeValue,
        BossAtom,
    )
    return {
        **BodyEvidence,
        "binding": "saved_configuration_atom_alias",
        "consumed_atom_id": BossAtom,
        "result_atom_id": CutAtom,
        "feature_scope_code": ScopeValue,
    }
