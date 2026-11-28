from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeFeatureA, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# omitted default children qualify only with the actual cold ownership and complete public root inventory
def CheckColdRows(
    Model: NativeModel,
    LinkValue: NativeLink,
    RootsValue: tuple[ArchiveNode, ...],
    MembersValue: tuple[ArchiveNode, ...],
    HelpersValue: tuple[Mapping[str, object], ...],
    ColdValue: ColdStockOwners,
) -> None:
    FieldsValue = LinkValue.ConfigValue.RootValue.FieldsValue
    ActualRoots = IndexFeatures(LinkValue)
    PublicIds = tuple(Value.object_id for Value in Model.features)
    if (
        ColdValue.LinkValue is not LinkValue
        or MembersValue
        or HelpersValue
        or FieldsValue.get("f1014") != 0
        or FieldsValue.get("f1018") is not None
        or FieldsValue.get("f13f8") is not None
        or len(RootsValue) != 23
        or len(PublicIds) != 23
        or len(set(PublicIds)) != len(PublicIds)
        or set(RootsValue) != set(ActualRoots.values())
        or set(PublicIds) != set(ActualRoots)
        or Model.features != tuple(sorted(Model.features, key=NativeFeatureA))
    ):
        raise ValueError(
            "cold two stock presentation has alternate roots or persisted system owners"
        )
