from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBodyTags import (
    CheckBodyTags,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadMgrAtom import (
    ReadMgrAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# a saved body identifier joins the registered archive producer to an actual kernel body
def CheckNamedAtom(
    LinkValue: NativeLink,
    BossValue: ArchiveNode,
    NodesValue: Mapping[int, XmtNode],
    Attributes: Mapping[str, XmtNode],
    LabelValue: str,
    ExplicitLabel: str | None,
) -> tuple[ArchiveNode, int]:
    AtomValue = ReadMgrAtom(LinkValue)
    if ReadOutputAtom(BossValue) is not AtomValue:
        raise ValueError("native output atom differs from the actual manager member")
    FeatureId = NativeNodeId(BossValue)
    CheckBodyTags(AtomValue, FeatureId, NodesValue, Attributes)
    if ExplicitLabel is None:
        if (
            AtomValue.FieldsValue.get("f18") is not None
            or AtomValue.FieldsValue.get("f18c") != 1
        ):
            raise ValueError("derived body has an unqualified authored atom name")
    elif (
        AtomValue.FieldsValue.get("f18c") != 0
        or ReadNativeName(AtomValue) != LabelValue
    ):
        raise ValueError("authored atom and kernel body names disagree")
    return AtomValue, FeatureId
