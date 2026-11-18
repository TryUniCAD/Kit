from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeFeature, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckThruRows import (
    CheckThruRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ThruTreeReport import (
    ThruTreeReport,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.TreeProjection import (
    TreeProjection,
)


# source presentation admission must retain every original public identity instead of collapsing its owned legacy rows
def ProjectThruTree(
    Model: NativeModel,
    LinkValue: NativeLink,
    Features: Mapping[int, NativeFeature],
    RootsValue: tuple[ArchiveNode, ...],
    RowsValue: tuple[Mapping[str, object], ...],
    MembersValue: tuple[ArchiveNode, ...],
    HelpersValue: tuple[Mapping[str, object], ...],
) -> TreeProjection:
    CheckThruRows(Model, LinkValue, RootsValue, MembersValue, HelpersValue)
    return TreeProjection(
        tuple(Features[Value.object_id] for Value in Model.features),
        ThruTreeReport(Model, RootsValue, RowsValue, MembersValue, HelpersValue),
    )
