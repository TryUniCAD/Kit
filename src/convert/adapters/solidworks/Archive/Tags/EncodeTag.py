from typing import cast as CastValue

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


# canonical native widths keep structural markers distinct from unsigned reference indices
def EncodeTag(TagValue: ArchiveTag) -> bytes:
    if type(TagValue) is not ArchiveTag:
        raise TypeError("archive tag value must be an archive tag")
    if type(CastValue(object, TagValue.KindValue)) is not str:
        raise TypeError("archive tag kind must be a string")
    if TagValue.KindValue in ("Null", "NewClass"):
        if TagValue.IndexValue is not None:
            raise ValueError("structural archive tags cannot carry a reference index")
        return KTagShort.pack(
            KTagNull if TagValue.KindValue == "Null" else KTagNewClass
        )
    if TagValue.KindValue not in ("ClassRef", "ObjectRef"):
        raise ValueError("archive tag kind is unsupported")
    IndexValue = TagValue.IndexValue
    if type(IndexValue) is not int:
        raise TypeError("archive reference index must be an integer")
    if not 1 <= IndexValue <= KTagWideClass - 1:
        raise ValueError("archive reference index exceeds the unsigned tag domain")
    if IndexValue < KTagWideMark:
        TagWord = IndexValue | (KTagClassBit if TagValue.KindValue == "ClassRef" else 0)
        return KTagShort.pack(TagWord)
    TagWord = IndexValue | (KTagWideClass if TagValue.KindValue == "ClassRef" else 0)
    return KTagShort.pack(KTagWideMark) + KTagLong.pack(TagWord)
