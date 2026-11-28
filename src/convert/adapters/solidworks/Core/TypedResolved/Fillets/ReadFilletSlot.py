from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import (
    ReadBodyScalar,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadKernelName import (
    ReadKernelName,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# historical body tracking must bind its live slot and implicit name to each actual modifier
def ReadFilletSlot(
    NodesValue: Mapping[int, XmtNode], AtomValue: ArchiveNode, Modifier: ArchiveNode
) -> tuple[XmtNode, XmtNode]:
    WorldValue = RequireXmt(NodesValue, 1, 101)
    (BodyIndex,) = WalkXmtChain(
        NodesValue, WorldValue.Integer("body"), 12, OwnerField="owner", OwnerValue=1
    )
    BodyValue = RequireXmt(NodesValue, BodyIndex, 12)
    if BodyValue.Integer("body_type") != 1 or any(
        BodyValue.Integer(NameValue)
        for NameValue in ("child", "ref_instance", "lattice", "mesh", "polyline")
    ):
        raise ValueError("SOLIDWORKS history body has an unqualified representation")
    AttrsValue = ReadBodyAttrs(NodesValue, BodyValue)
    TagValue = ReadBodyScalar(NodesValue, AttrsValue, "BODY_MATCH", 0)
    AtomId = ReadBodyScalar(NodesValue, AttrsValue, "ATOM_ID_2001", 1)
    ModifierId = ReadBodyScalar(
        NodesValue, AttrsValue, "LAST_BODY_MODIFYING_FEATURE_ID", 1
    )
    Fields = AtomValue.FieldsValue
    if (
        TagValue <= 0
        or AtomId <= 0
        or TagValue != Fields.get("f180")
        or TagValue != Fields.get("f1b0")
        or AtomId != Fields.get("f140")
        or ModifierId != NativeNodeId(Modifier)
        or ReadKernelName(NodesValue, AttrsValue) != (ReadNativeName(Modifier), None)
    ):
        raise ValueError("SOLIDWORKS rollback body is foreign to the recorded modifier")
    NameIndex = AttrsValue["SWIMPLICITBODYNAME_ID_U"].Indexes("fields")[0]
    return BodyValue, RequireXmt(NodesValue, NameIndex, 98)
