from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import (
    KEnvFolderClass,
    KSceneChildTypes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# only the scene role allows bounded children before the owner fields validate their links
def ReadMemBodyMut(
    ContextValue: BodyContext,
    MemberClass: RuntimeClass,
    ReaderValue: GraphReader,
    NodeValue: ArchiveNode,
) -> None:
    DepthValue = ReaderValue.NestingDepth
    if DepthValue == 1:
        Allowed = NodeValue.ClassValue == MemberClass
    else:
        ChildTypes = KSceneChildTypes.get(DepthValue)
        Allowed = (
            MemberClass == KEnvFolderClass
            and ChildTypes is not None
            and NodeValue.ClassValue in ChildTypes
        )
    if not Allowed:
        raise BodyUnsupported(
            "SOLIDWORKS configuration member has an unsupported body owner"
        )
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
