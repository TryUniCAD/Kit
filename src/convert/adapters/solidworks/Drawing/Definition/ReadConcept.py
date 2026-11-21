from functools import partial as PartialValue

from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadTypedNode import ReadTypedMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Definition.ConceptState import ConceptState
from convert.adapters.solidworks.Drawing.Definition.ReadConceptBody import (
    ReadConceptBody,
)
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import (
    KDefinitionStream,
    KDrawArchiveVersion,
    KDrawClsid,
    KDrawClsidOffset,
)


# release checked drawing layout uses one archive map through the first resolved concept
def ReadConcept(Archive: SldprtArchive, Version: int) -> ArchiveNode:
    if Version != KDrawArchiveVersion:
        raise ValueError(f"unqualified drawing concept version {Version}")
    Cursor = BinaryReader(Archive.require(KDefinitionStream))
    _ = Cursor.TakeBytes(KDrawClsidOffset)
    if Cursor.TakeBytes(len(KDrawClsid)) != KDrawClsid:
        raise ValueError("drawing concept has an unsupported document CLSID")
    Graph = GraphReader(
        Cursor, ArchiveMaps(1), PartialValue(ReadConceptBody, ConceptState())
    )
    RootValue = ReadTypedMut(Graph, "moDrawing_c")
    if RootValue is None or Cursor.GetRemaining() == 0:
        raise ValueError(
            "drawing Definition lacks the expected concept or resolved tail"
        )
    return RootValue
