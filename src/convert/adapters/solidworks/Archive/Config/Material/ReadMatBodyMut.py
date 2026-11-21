from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.Material.CheckMatBody import (
    CheckMatBody,
)
from convert.adapters.solidworks.Archive.Config.Material.MatTypes import (
    KDensityClass,
    KMaterialClass,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# only the material record may descend into a density child in this suffix
def ReadMatBodyMut(
    ContextValue: BodyContext,
    RootClass: RuntimeClass,
    ReaderValue: GraphReader,
    NodeValue: ArchiveNode,
) -> None:
    DepthValue = ReaderValue.NestingDepth
    ExpectedClass = (
        KDensityClass if DepthValue == 2 and RootClass == KMaterialClass else None
    )
    if DepthValue == 1:
        ExpectedClass = RootClass
    if NodeValue.ClassValue != ExpectedClass:
        raise BodyUnsupported("unsupported SOLIDWORKS lightweight material body owner")
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
    CheckMatBody(NodeValue)
