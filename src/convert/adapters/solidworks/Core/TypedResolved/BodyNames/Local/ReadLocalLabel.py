from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import (
    ReadBodyScalar,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadImplicitName import (
    ReadImplicit,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadKernelName import (
    ReadKernelName,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# local labels distinguish the feature key from the explicitly named archive atom
def ReadLocalLabel(
    NodesValue: Mapping[int, XmtNode],
    Attributes: Mapping[str, XmtNode],
    AtomValue: ArchiveNode,
    FeatureId: int,
    GroupKey: str,
) -> tuple[str, str]:
    AtomFields = AtomValue.FieldsValue
    if Attributes and (
        ReadBodyScalar(NodesValue, Attributes, "ATOM_ID_2001", 1) != AtomFields["f140"]
        or ReadBodyScalar(NodesValue, Attributes, "LAST_BODY_MODIFYING_FEATURE_ID", 1)
        != FeatureId
        or (
            "BODY_MATCH" in Attributes
            and ReadBodyScalar(NodesValue, Attributes, "BODY_MATCH", 0)
            != AtomFields["f180"]
        )
    ):
        raise ValueError("local kernel and archive tracking owners disagree")
    if "SDL/TYSA_UNAME" in Attributes or "SW_INTERNAL_BODY_NAME" in Attributes:
        raise ValueError("local body has an unqualified alternate name owner")
    if AtomFields.get("f18") is None and AtomFields.get("f18c") == 1:
        if not Attributes:
            if any(NodeValue.KindValue == 81 for NodeValue in NodesValue.values()):
                raise ValueError("local key naming requires an entirely bare body")
            return GroupKey, "local_storage_key"
        if (
            "SDL/TYSA_NAME" in Attributes
            or ReadImplicit(NodesValue, Attributes) != GroupKey
        ):
            raise ValueError("derived local body name disagrees with its storage key")
        return GroupKey, "implicit_kernel_and_key"
    if AtomFields.get("f18") is None or AtomFields.get("f18c") != 0:
        raise ValueError("local body has an unqualified atom name state")
    Authored = ReadNativeName(AtomValue)
    LabelValue, Explicit = ReadKernelName(NodesValue, Attributes, Authored)
    if Explicit != Authored or LabelValue != Authored:
        raise ValueError("authored local body name disagrees with its kernel owner")
    return LabelValue, "authored_atom_and_kernel"
