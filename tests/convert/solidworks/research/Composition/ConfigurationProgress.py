from __future__ import annotations

from importlib import import_module as ImportModule

from convert.adapters.solidworks.container.Container import SldprtArchive
from tests.convert.solidworks.research.Composition.NodeFields import ReadFields

# persisted progress must be decoded through the initialized research registry
KLoadRooted = ImportModule("Streams").load_rooted


# current configuration state must agree with the independently stored native header counter
def IsProgressValid(ArchiveFile: SldprtArchive, CodecReg: object) -> bool:
    HeaderDocu, HeaderReader = KLoadRooted(
        ArchiveFile.require("Header2"), CodecReg, 1, 19000
    )
    ManagerDocu, ManagerReader = KLoadRooted(
        ArchiveFile.require("Contents/CMgr"), CodecReg, 1, 19000
    )
    if (
        HeaderDocu.tail
        or ManagerDocu.tail
        or HeaderReader.left()
        or ManagerReader.left()
    ):
        raise RuntimeError("configuration progress decoding has unread bytes")
    NextId = ReadFields(HeaderDocu.roots[0])["f08"]
    ActiveConfig = ReadFields(ManagerDocu.roots[0])["f360"]
    HighestId = ReadFields(ActiveConfig)["f85c"]
    if type(NextId) is not int or type(HighestId) is not int:
        raise TypeError("configuration progress and header ids must be integers")
    return HighestId == NextId - 1
