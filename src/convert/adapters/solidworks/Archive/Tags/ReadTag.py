from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag

from convert.adapters.solidworks.Archive.Tags.TagField import (
    KTagShort,
    KTagLong,
    KTagNull,
    KTagNewClass,
    KTagWideMark,
    KTagClassBit,
    KTagWideClass,
)


# native tag boundaries must remain independent of descriptor and object allocation
def ReadTag(
    BufferValue: bytes, OffsetValue: int, *, LimitValue: int | None = None
) -> tuple[ArchiveTag, int]:
    if type(BufferValue) is not bytes:
        raise TypeError("archive tag input must be bytes")
    if type(OffsetValue) is not int:
        raise TypeError("archive tag position must be an integer")
    EndValue = len(BufferValue) if LimitValue is None else LimitValue
    if OffsetValue < 0 or not OffsetValue + KTagShort.size <= EndValue <= len(
        BufferValue
    ):
        raise ValueError("archive tag has no complete unsigned short")
    TagWord = int(KTagShort.unpack_from(BufferValue, OffsetValue)[0])
    NextOffset = OffsetValue + KTagShort.size
    if TagWord == KTagNewClass:
        return ArchiveTag("NewClass", None), NextOffset
    if TagWord == KTagWideMark:
        if NextOffset + KTagLong.size > EndValue:
            raise ValueError("archive tag has no complete unsigned dword")
        TagWord = int(KTagLong.unpack_from(BufferValue, NextOffset)[0])
        NextOffset += KTagLong.size
        ClassMask = KTagWideClass
    else:
        ClassMask = KTagClassBit
    IndexValue = TagWord & (ClassMask - 1)
    if TagWord & ClassMask:
        if IndexValue == KTagNull:
            raise ValueError("archive class reference cannot use reserved index zero")
        return ArchiveTag("ClassRef", IndexValue), NextOffset
    if IndexValue == KTagNull:
        return ArchiveTag("Null", None), NextOffset
    return ArchiveTag("ObjectRef", IndexValue), NextOffset
