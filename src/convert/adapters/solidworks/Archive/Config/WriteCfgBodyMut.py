from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KSketchBlockClass,
)
from convert.adapters.solidworks.Archive.Config.Members.CheckBlockOwner import (
    CheckBlockOwner,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# configuration emission rejects the same foreign block owners as the reader
def WriteCfgBodyMut(WriterValue: BodyWriter, NodeValue: ArchiveNode) -> None:
    if NodeValue.ClassValue == KSketchBlockClass:
        CheckBlockOwner(NodeValue, RequireEmpty=False)
    WriteBodyMut(WriterValue, NodeValue)
