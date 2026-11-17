from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import (
    ReadTagMut,
    ReadTypeDescMut,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KComponentTreeStream,
    KitDocStream,
    PartLaneNames,
)
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat

# drawing identity uses the native definition prefix rather than a filename heuristic
KDefinitionStream = "Contents/Definition"


# the native model document prefix introduces a separate drawing class identity
KDrawClsid = bytes.fromhex("343da383c527ce11bfd400400513bb57")


# the ordinary drawing archive grammar has a proven release boundary
KDrawArchiveVersion = 19000


# the document writer serializes five longs before its native class identifier
KDrawClsidOffset = 20


# the archive classification lets known drawing sources reach the correct reader
def HasDrawingClsid(Archive: SldprtArchive) -> bool:
    Definition = Archive.get(KDefinitionStream)
    EndOffset = KDrawClsidOffset + len(KDrawClsid)
    return (
        Definition is not None and Definition[KDrawClsidOffset:EndOffset] == KDrawClsid
    )


# a valid drawing must have its own model root and unambiguous stream identity
def CheckDrawLane(Archive: SldprtArchive) -> int:
    StreamNames = Archive.streams
    Version = ContainerMo(StreamNames)
    if Archive.format_version != 4 or Version != KDrawArchiveVersion:
        raise SldprtFormat(
            "drawing inspection requires SOLIDWORKS model archive version 19000"
        )
    if f"_MO_VERSION_{Version}/History" not in StreamNames:
        raise SldprtFormat("drawing inspection requires its native history stream")
    if (
        KitDocStream in StreamNames
        or KComponentTreeStream in StreamNames
        or PartLaneNames(StreamNames)
    ):
        raise SldprtFormat("drawing has conflicting document lanes")
    Definition = Archive.require(KDefinitionStream)
    if not HasDrawingClsid(Archive):
        raise SldprtFormat("drawing Definition CLSID is missing")
    Offset = KDrawClsidOffset + len(KDrawClsid)
    Cursor = BinaryReader(Definition, Offset)
    if ReadTagMut(Cursor).KindValue != "NewClass":
        raise SldprtFormat("drawing Definition has no new native model root")
    RootValue = ReadTypeDescMut(Cursor)
    if (RootValue.NameValue, RootValue.SchemaValue) != ("moDrawing_c", 1):
        raise SldprtFormat("drawing Definition root requires moDrawing_c schema one")
    if Cursor.GetRemaining() < 10 or Definition[-10:-8] != b"\xaf\x0d":
        raise SldprtFormat("drawing Definition trailer is unsupported")
    return KDrawArchiveVersion
