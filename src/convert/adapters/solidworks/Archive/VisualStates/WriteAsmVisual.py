from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.CheckExtShape import CheckExtShape
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Archive.VisualStates.VisualFields import (
    KVisualFields,
    KVisualSchemas,
)

# the measured assembly visibility owner is independent of the component instance xml
KVisualStream = "ThirdPtyStore/VisualStates"


# detached visual targets have a separate parent chain from the ordinary manager body writer
def WriteVisNodeMut(WriterValue: BodyWriter, NodeValue: ArchiveNode) -> None:
    if NodeValue.ClassValue == RuntimeClass("moExtFeature_c", 1):
        if tuple(WriterValue.ContextValue.UsageValue.SchemaPath) != (
            "visStateKeyData_c",
            "moContextChainComponent_c",
            "moChainComponent_c",
            "moReferenceChain_c",
            "moExtFeatureList_c",
        ):
            raise ValueError("assembly visual external target has a foreign owner")
        CheckExtShape(NodeValue.FieldsValue)
    WriteBodyMut(WriterValue, NodeValue)


# visibility stores own their map independently of the assembly configuration and resolved archive maps
def WriteAsmVisual(RootValue: ArchiveNode) -> bytes:
    if (
        RootValue.ClassValue != RuntimeClass("visStateKeyData_c", 1)
        or RootValue.FieldsValue.get("n") != 0
        or RootValue.FieldsValue.get("f88") != ()
    ):
        raise ValueError("assembly visual store requires its ordinary empty tracker")
    ContextValue = BodyContext(
        19000, KVisualFields, {}, KVisualSchemas, FlagsValue={"conditions": 0x20004000}
    )
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteVisNodeMut)
    WriterValue.OutputValue.extend(EncodeScalar(ContextValue.VersionValue, "u32"))
    WriterValue.OutputValue.extend(EncodeScalar(0, "i32"))
    WriteNodeMut(WriterValue, RootValue)
    return bytes(WriterValue.OutputValue)
