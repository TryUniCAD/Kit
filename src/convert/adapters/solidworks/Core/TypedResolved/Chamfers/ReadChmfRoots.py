from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckExtras import (
    CheckExtras,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ConfigHelpers import (
    ReadConfigHelp,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.OwnedRows import (
    ReadOwnedRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.RootOrder import (
    ReadRootOrder,
)


# presentation rooting keeps the whole ordinary stock prefix and its one actual new modeling feature
def ReadChmfRoots(
    LinkValue: NativeLink,
    ModelValue: NativeModel,
    ChmfValue: ArchiveNode,
) -> tuple[tuple[ArchiveNode, ...], dict[int, ArchiveNode]]:
    Resolved = LinkValue.ResolvedValue
    if (
        Resolved.ExtraFields != {"n": 0, "fcd8": []}
        or Resolved.RootsValue[-1] is not ChmfValue
    ):
        raise ValueError(
            "chamfer requires the exact fresh end of the ordinary stock root sequence"
        )
    Prefix = ReplaceValue(
        LinkValue,
        ResolvedValue=ReplaceValue(Resolved, RootsValue=Resolved.RootsValue[:-1]),
    )
    Nodes = IndexFeatures(Prefix)
    Roots = (*ReadRootOrder(Prefix, Nodes), ChmfValue)
    NativeId = NativeNodeId(ChmfValue)
    if NativeId in Nodes:
        raise ValueError(
            "chamfer feature repeats an actual earlier stock root identity"
        )
    Nodes[NativeId] = ChmfValue
    Members: tuple[ArchiveNode, ...] = ()
    for NodeValue in Roots:
        if NodeValue.ClassValue.NameValue in ("moDetailCabinet_c", "moEnvFolder_c"):
            _, Owned = ReadOwnedRows(LinkValue, NodeValue)
            Members += Owned
    CheckExtras(ModelValue, Roots, Members, ReadConfigHelp(LinkValue))
    if set(Nodes) != {Feature.object_id for Feature in ModelValue.features}:
        raise ValueError(
            "chamfer cannot project unrepresented alternate feature presentation"
        )
    CheckTreeAlias(LinkValue, Roots)
    return Roots, Nodes
