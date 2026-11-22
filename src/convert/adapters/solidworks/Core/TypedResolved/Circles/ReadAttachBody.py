from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.CheckAttachGeom import (
    CheckAttachGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.CheckAttachIds import (
    CheckAttachIds,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.CheckBodyMarks import (
    CheckBodyMarks,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.ReadAttachName import (
    ReadAttachName,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.ReadAttachPart import (
    ReadAttachPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.ReadAttachSolid import (
    ReadAttachSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadAttachAtom import (
    ReadAttachAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadAttachAttr import (
    ReadAttachAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# the attached name depends on the same physical solid live dimensions and archive owners
def ReadAttachBody(
    LinkValue: NativeLink,
    BossValue: ArchiveNode,
    BodyId: int,
    Partition: bytes,
    ModelValue: NativeModel,
    *,
    SavedBody: bool,
) -> str:
    BodyTag = ReadAttachAtom(LinkValue, BossValue, BodyId, SavedBody=SavedBody)
    Active, History, Nodes = ReadAttachPart(Partition)
    CheckBodyMarks(LinkValue, BossValue, ReadHistMarks(History, Nodes))
    BodyNode = ReadAttachSolid(Nodes)
    Attrs = ReadAttachAttrs(Nodes, BodyNode)
    CheckAttachIds(
        Attrs,
        BodyId,
        BodyTag,
        NativeNodeId(BossValue),
        LinkValue.ConfigValue.HeaderValue.FieldsValue.get("f44"),
    )
    CheckAttachGeom(Active, ModelValue)
    return ReadAttachName(Attrs)
