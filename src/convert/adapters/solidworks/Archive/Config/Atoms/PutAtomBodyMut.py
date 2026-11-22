from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Config.Atoms.AtomTypes import KAtomClass
from convert.adapters.solidworks.Archive.Config.Atoms.CheckAtomBody import CheckAtomBody
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# generated manager rows can introduce only the bounded concrete atom
def PutAtomBodyMut(WriterValue: BodyWriter, NodeValue: ArchiveNode) -> None:
    if WriterValue.NestingDepth != 1 or NodeValue.ClassValue != KAtomClass:
        raise BodyUnsupported("unsupported SOLIDWORKS atom body owner")
    if (
        NodeValue.IndexValue is not None
        and ObjectIndex(WriterValue.MapValue, NodeValue) != NodeValue.IndexValue
    ):
        raise BodyUnsupported(
            "SOLIDWORKS atom emission would change its native map index"
        )
    CheckAtomBody(NodeValue)
    WriteBodyMut(WriterValue, NodeValue)
