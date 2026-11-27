from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.Current.Attributed.AttributedNullFields import (
    KAttributedNullFields,
)
from convert.adapters.solidworks.Archive.Partition.Current.Attributed.CheckActiveRefs import (
    CheckActiveRefs,
)
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.Current.Attributed.CheckActiveFins import (
    CheckActiveFins,
)
from convert.adapters.solidworks.Core.Partition.Current.Attributed.CheckFacePlanes import (
    CheckFacePlanes,
)
from convert.adapters.solidworks.Core.Partition.Current.Attributed.CheckOwnedLines import (
    CheckOwnedLines,
)
from convert.adapters.solidworks.Core.Partition.Current.Attributed.CheckFreeTrims import (
    CheckFreeTrims,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import (
    ReadBodyTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalGeom import (
    CheckLocalGeom,
)


# separate active ownership is necessary before local topology builders can consume these records
def CheckActiveBody(
    Nodes: Mapping[int, XmtNode],
) -> tuple[XmtNode, dict[int, set[int]]]:
    CheckActiveRefs(Nodes)
    Kinds: dict[int, set[int]] = {}
    for NodeValue in Nodes.values():
        Kinds.setdefault(NodeValue.KindValue, set()).add(NodeValue.IndexValue)
        if any(
            NodeValue.Integer(NameValue)
            for NameValue in KAttributedNullFields.get(NodeValue.KindValue, ())
        ):
            raise ValueError("attributed active graph has an alternate attachment")
    TreeValue = ReadBodyTree(Nodes)
    BodyValue = Nodes[TreeValue.BodyIndex]
    SolidShell = BodyValue.Integer("shell")
    for ShellId in Kinds[13]:
        FaceField = "front_face" if ShellId == SolidShell else "face"
        if Nodes[ShellId].Integer(FaceField):
            raise ValueError("attributed active shell has an alternate face attachment")
    if BodyValue.Integer("state") != 1 or BodyValue.Integer("nom_geom_state") != 1:
        raise ValueError("attributed active body has an unsupported geometry state")
    for KindValue, NameValue, Owned in (
        (16, "edge", True),
        (18, "vertex", True),
        (29, "boundary_point", False),
        (30, "boundary_curve", False),
        (50, "boundary_surface", False),
    ):
        Members = WalkXmtChain(
            Nodes,
            BodyValue.Integer(NameValue),
            KindValue,
            OwnerField="owner" if Owned else None,
            OwnerValue=BodyValue.IndexValue if Owned else None,
        )
        if set(Members) != Kinds[KindValue]:
            raise ValueError("attributed active body inventory is incomplete")
    CheckLocalGeom(Nodes, Kinds)
    CheckActiveFins(Nodes, TreeValue.FinIds)
    CheckOwnedLines(Nodes, TreeValue.EdgeIds)
    CheckFacePlanes(Nodes, TreeValue.FaceIds)
    CheckFreeTrims(Nodes, BodyValue, Kinds)
    return BodyValue, Kinds
