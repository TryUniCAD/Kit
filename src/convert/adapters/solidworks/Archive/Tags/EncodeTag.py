from struct import pack as PackValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag


# canonical native widths keep structural markers distinct from unsigned reference indices
def EncodeTag(TagValue: ArchiveTag) -> bytes:
    if type(TagValue) is not ArchiveTag:
        raise TypeError("archive tag value must be an archive tag")
    if type(CastValue(object, TagValue.KindValue)) is not str:
        raise TypeError("archive tag kind must be a string")
    if TagValue.KindValue in ("Null", "NewClass"):
        if TagValue.IndexValue is not None:
            raise ValueError("structural archive tags cannot carry a reference index")
        return PackValue("<H", 0 if TagValue.KindValue == "Null" else 0xFFFF)
    if TagValue.KindValue not in ("ClassRef", "ObjectRef"):
        raise ValueError("archive tag kind is unsupported")
    IndexValue = TagValue.IndexValue
    if type(IndexValue) is not int:
        raise TypeError("archive reference index must be an integer")
    if not 1 <= IndexValue <= 0x7FFFFFFF:
        raise ValueError("archive reference index exceeds the unsigned tag domain")
    if IndexValue < 0x7FFF:
        TagWord = IndexValue | (0x8000 if TagValue.KindValue == "ClassRef" else 0)
        return PackValue("<H", TagWord)
    TagWord = IndexValue | (0x80000000 if TagValue.KindValue == "ClassRef" else 0)
    return PackValue("<HI", 0x7FFF, TagWord)
