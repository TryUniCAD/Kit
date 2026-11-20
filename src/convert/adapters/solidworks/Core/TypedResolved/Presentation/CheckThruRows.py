from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# retained source identities must cover persisted roots members and the actual empty configuration helper exactly
def CheckThruRows(
    Model: NativeModel,
    LinkValue: NativeLink,
    RootsValue: tuple[ArchiveNode, ...],
    MembersValue: tuple[ArchiveNode, ...],
    HelpersValue: tuple[Mapping[str, object], ...],
    *,
    TwoStocks: bool = False,
) -> None:
    FieldsValue = LinkValue.ConfigValue.RootValue.FieldsValue
    HelperKinds: tuple[str, ...] = ("moPrtExplViewManager_c",)
    if TwoStocks and FieldsValue.get("f1014") == 1:
        MasterValue = RequireNative(FieldsValue.get("f1018"), "moSheetMetalMaster_c")
        if MasterValue.IndexValue is not None:
            raise ValueError("embedded sheet-metal master carries archive map identity")
        HelperKinds = ("moSheetMetalMaster_c", *HelperKinds)
    ActualKinds = tuple(Value["class"] for Value in HelpersValue)
    if len(MembersValue) != 6 or ActualKinds != HelperKinds:
        raise ValueError(
            "through-all source requires all actual persisted system owners"
        )
    HelperValue = RequireNative(
        LinkValue.ConfigValue.RootValue.FieldsValue.get("f13f8"),
        "moPrtExplViewManager_c",
    )
    CheckTreeAlias(LinkValue, (*MembersValue, HelperValue))
    OwnerIds = (
        *(NativeNodeId(Value) for Value in RootsValue),
        *(NativeNodeId(Value) for Value in MembersValue),
        *(Value["stored_node_id"] for Value in HelpersValue),
    )
    PublicIds = tuple(Value.object_id for Value in Model.features)
    if len(set(OwnerIds)) != len(OwnerIds) or set(OwnerIds) != set(PublicIds):
        raise ValueError("through-all source has stripped or unaccounted public owners")
