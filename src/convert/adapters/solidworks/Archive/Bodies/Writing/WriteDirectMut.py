from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# direct part header aliases reserve real map slots without emitting an object body
def WriteDirectMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Writer = FrameValue.WriterValue
    Context = Writer.ContextValue
    MapValue = Writer.MapValue
    Owner = FrameValue.NodeValue
    if (
        Context.VersionValue != KHeaderVersion
        or Owner.ClassValue != RuntimeClass("moPart_c", 1)
        or FrameValue.ScopeValue.ParentValue is not None
        or Writer.NestingDepth != 1
        or ObjectIndex(MapValue, Owner) is None
    ):
        raise BodyUnsupported("unsupported SOLIDWORKS direct part header owner")
    Nodes = tuple(
        ArchiveNode.RequireNode(NodeValue) for NodeValue in Context.DirectNodes
    )
    if (
        not Nodes
        or len(set(Nodes)) != len(Nodes)
        or any(
            NodeValue.ClassValue != RuntimeClass("moExtObject_c", 1)
            or ObjectIndex(MapValue, NodeValue) is not None
            for NodeValue in Nodes
        )
    ):
        raise BodyUnsupported(
            "SOLIDWORKS direct part header needs distinct new aliases"
        )
    BindNodesMut(FrameValue.WriterValue.MapValue, Nodes)
