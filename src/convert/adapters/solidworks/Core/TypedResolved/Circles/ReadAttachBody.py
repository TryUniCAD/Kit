from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadAttachAtom import (
    ReadAttachAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadAttachAttr import (
    ReadAttachAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# native marks must bind the actual selected partition and originating activation across both streams
def CheckBodyMarks(
    LinkValue: NativeLink, BossValue: ArchiveNode, Marks: tuple[int, int]
) -> None:
    Selected = RequireNative(BossValue.FieldsValue.get("f3d0"), "moPMarkRecord_c")
    Activation = RequireNative(
        LinkValue.ConfigValue.RootValue.FieldsValue.get("fe38"), "moPMarkRecord_c"
    )
    if (Selected.FieldsValue.get("f18"), Activation.FieldsValue.get("f18")) != Marks:
        raise ValueError(
            "SOLIDWORKS attached circle marks disagree with native history"
        )


# a radius boss can project its live geometry only after the physical body and rollback agree with both archive owners
def ReadAttachBody(
    LinkValue: NativeLink,
    BossValue: ArchiveNode,
    BodyId: int,
    Partition: bytes,
    *,
    SavedBody: bool,
) -> str:
    BodyTag = ReadAttachAtom(LinkValue, BossValue, BodyId, SavedBody=SavedBody)
    Active, History = DecodePartition(Partition, KPartitionStream)
    if (Active.kind, History.kind) != ("partition", "deltas"):
        raise ValueError(
            "SOLIDWORKS attached circle lacks its unique active and rollback states"
        )
    Nodes = ReadActiveNodes(Active.data)
    CheckXmtGraph(Nodes)
    CheckBodyMarks(LinkValue, BossValue, ReadHistMarks(History.data, Nodes))
    World = RequireXmt(Nodes, 1, 101)
    BodyNode = RequireXmt(Nodes, World.Integer("body"), 12)
    if (
        BodyNode.Integer("owner"),
        BodyNode.Integer("body_type"),
        BodyNode.Integer("next"),
    ) != (
        1,
        1,
        0,
    ) or sum(
        NodeValue.KindValue == 12 for NodeValue in Nodes.values()
    ) != 1:
        raise ValueError(
            "SOLIDWORKS attached circle requires its one active world solid"
        )
    _ = ReadBodyFaces(Nodes, BodyNode, 3)
    Attrs = ReadAttachAttrs(Nodes, BodyNode)
    if (
        Attrs.get("ATOM_ID_2001") != (BodyId,)
        or Attrs.get("LAST_BODY_MODIFYING_FEATURE_ID") != (NativeNodeId(BossValue),)
        or Attrs.get("BODY_MATCH") != (BodyTag,)
        or Attrs.get("ENT_TIME_STAMP_2001")
        != (LinkValue.ConfigValue.HeaderValue.FieldsValue.get("f44"),)
    ):
        raise ValueError(
            "SOLIDWORKS attached circle body attributes disagree with archive ownership"
        )
    Label = b"".join(
        UnitValue.to_bytes(2, "little")
        for UnitValue in Attrs["SWIMPLICITBODYNAME_ID_U"]
    ).decode("utf-16-le")
    if (
        not Label
        or "\x00" in Label
        or any(
            NameValue in Attrs
            for NameValue in (
                "SDL/TYSA_NAME",
                "SDL/TYSA_UNAME",
                "SW_INTERNAL_BODY_NAME",
            )
        )
    ):
        raise ValueError("SOLIDWORKS attached circle has an invalid implicit body name")
    return Label
