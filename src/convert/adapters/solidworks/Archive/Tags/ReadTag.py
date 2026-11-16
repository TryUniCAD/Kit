from struct import unpack_from as UnpackValue

from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag


# native tag boundaries must remain independent of descriptor and object allocation
def ReadTag(BufferValue: bytes, OffsetValue: int) -> tuple[ArchiveTag, int]:
    if type(BufferValue) is not bytes:
        raise TypeError("archive tag input must be bytes")
    if type(OffsetValue) is not int:
        raise TypeError("archive tag position must be an integer")
    if OffsetValue < 0 or OffsetValue + 2 > len(BufferValue):
        raise ValueError("archive tag has no complete unsigned short")
    TagWord = int(UnpackValue("<H", BufferValue, OffsetValue)[0])
    NextOffset = OffsetValue + 2
    if TagWord == 0xFFFF:
        return ArchiveTag("NewClass", None), NextOffset
    if TagWord == 0x7FFF:
        if NextOffset + 4 > len(BufferValue):
            raise ValueError("archive tag has no complete unsigned dword")
        TagWord = int(UnpackValue("<I", BufferValue, NextOffset)[0])
        NextOffset += 4
        ClassMask = 0x80000000
    else:
        ClassMask = 0x8000
    IndexValue = TagWord & (ClassMask - 1)
    if TagWord & ClassMask:
        if IndexValue == 0:
            raise ValueError("archive class reference cannot use reserved index zero")
        return ArchiveTag("ClassRef", IndexValue), NextOffset
    if IndexValue == 0:
        return ArchiveTag("Null", None), NextOffset
    return ArchiveTag("ObjectRef", IndexValue), NextOffset
