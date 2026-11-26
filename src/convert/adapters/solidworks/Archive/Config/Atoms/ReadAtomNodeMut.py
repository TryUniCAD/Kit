from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.Atoms.AtomTypes import KAtomClass
from convert.adapters.solidworks.Archive.Config.Atoms.CheckAtomBody import CheckAtomBody
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# only the concrete atom class can descend from this embedded manager record
def ReadAtomNodeMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, NodeValue: ArchiveNode
) -> None:
    if ReaderValue.NestingDepth != 1 or NodeValue.ClassValue != KAtomClass:
        raise BodyUnsupported("unsupported SOLIDWORKS atom body owner")
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
    CheckAtomBody(NodeValue)
