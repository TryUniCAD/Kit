from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeFeature, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.BindTreeRoot import (
    BindTreeRoot,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckExtras import (
    CheckExtras,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ConfigHelpers import (
    ReadConfigHelp,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.NativeRow import (
    MakeNativeRow,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.OwnedRows import (
    ReadOwnedRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ProjectThruTree import (
    ProjectThruTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.RootOrder import (
    ReadRootOrder,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.TreeProjection import (
    TreeProjection,
)


# the narrow native presentation profile must never discard an unclassified authored feature or imply universal parity
def ProjectTree(
    Model: NativeModel,
    LinkValue: NativeLink,
    NodesValue: Mapping[int, ArchiveNode],
    Features: Mapping[int, NativeFeature],
    *,
    TwoStocks: bool = False,
    ColdValue: ColdStockOwners | None = None,
) -> TreeProjection:
    Original = tuple(Features[Feature.object_id] for Feature in Model.features)
    try:
        RootsValue = ReadRootOrder(LinkValue, NodesValue, TwoStocks=TwoStocks)
        RowsValue: list[Mapping[str, object]] = []
        MembersValue: tuple[ArchiveNode, ...] = ()
        for NodeValue in RootsValue:
            RowsValue.append(MakeNativeRow(LinkValue, NodeValue))
            if NodeValue.ClassValue.NameValue in ("moDetailCabinet_c", "moEnvFolder_c"):
                ChildRows, ChildNodes = ReadOwnedRows(LinkValue, NodeValue)
                RowsValue.extend(ChildRows)
                MembersValue += ChildNodes
        HelpersValue = ReadConfigHelp(LinkValue)
        CheckExtras(Model, RootsValue, MembersValue, HelpersValue)
        if RootsValue[-1].ClassValue.NameValue == "moICE_c":
            ThroughTree = ProjectThruTree(
                Model,
                LinkValue,
                Features,
                RootsValue,
                tuple(RowsValue),
                MembersValue,
                HelpersValue,
                TwoStocks=TwoStocks,
                ColdValue=ColdValue,
            )
            if ColdValue is not None:
                return ReplaceValue(
                    ThroughTree,
                    EvidenceValue={
                        **ThroughTree.EvidenceValue,
                        "status": "ordinary_cold_selected_two_stock_profile",
                        "profile": "solidworks_2026_english_cold_selected_through_cut",
                        "parametric_timeline_stable": True,
                    },
                )
            if TwoStocks:
                return ReplaceValue(
                    ThroughTree,
                    EvidenceValue={
                        **ThroughTree.EvidenceValue,
                        "status": "ordinary_selected_two_stock_profile",
                        "parametric_timeline_stable": True,
                    },
                )
            return ThroughTree
    except (ValueError, TypeError, KeyError) as ErrorValue:
        return TreeProjection(
            Original,
            {"status": "unqualified", "diagnostic": str(ErrorValue)},
        )
    return TreeProjection(
        tuple(
            (
                Features[NativeNodeId(NodeValue)]
                if RootsValue[-1].ClassValue.NameValue == "moRevolution_c"
                else BindTreeRoot(Features[NativeNodeId(NodeValue)], NodeValue)
            )
            for NodeValue in RootsValue
        ),
        {
            "status": "ordinary_default_profile",
            "rows": tuple(RowsValue),
            "configuration_helpers": HelpersValue,
            "parametric_timeline_stable": True,
            "profile": "solidworks_2026_english_default_session",
            "comparison_scope": ("name", "type", "parent", "order"),
            "implicit_default_state_encoded": False,
            "native_status_flags_qualified": False,
            "arbitrary_session_defaults_qualified": False,
            "custom_tree_layouts_qualified": False,
            "authored_caption_parity_qualified": False,
            "full_native_tree_qualified": False,
        },
    )
