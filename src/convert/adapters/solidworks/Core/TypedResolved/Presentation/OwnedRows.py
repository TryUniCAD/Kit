from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.DefaultRows import (
    KDefaultMembers,
    MakeDefaultRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.NativeRow import (
    MakeNativeRow,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# only the proven empty or default owned collections may change the ordinary public timeline
def ReadOwnedRows(
    LinkValue: NativeLink, OwnerValue: ArchiveNode
) -> tuple[tuple[Mapping[str, object], ...], tuple[ArchiveNode, ...]]:
    Children = ReadChildren(OwnerValue)
    ClassName = OwnerValue.ClassValue.NameValue
    if not Children:
        return MakeDefaultRows(OwnerValue), ()
    Defaults = KDefaultMembers[ClassName]
    if tuple(
        (ReadNativeName(Child), Child.ClassValue.NameValue) for Child in Children
    ) != tuple((NameValue, TypeValue) for _, NameValue, TypeValue in Defaults):
        raise ValueError("authored system children are outside the default profile")
    if any(ReadChildren(Child) for Child in Children):
        raise ValueError("populated system children retain their existing semantics")
    if ClassName == "moDetailCabinet_c":
        HeadValue, TailValue = Children
        if (
            HeadValue.FieldsValue.get("f37c") != 1
            or TailValue.FieldsValue.get("f37c") != 0
            or HeadValue.FieldsValue.get("f388") is not TailValue
            or TailValue.FieldsValue.get("f388") is not HeadValue
        ):
            raise ValueError("notes folder lacks the native head and end partnership")
    return (
        tuple(
            MakeNativeRow(LinkValue, Child, OwnerValue, Default[0])
            for Child, Default in zip(Children, Defaults, strict=True)
        ),
        Children,
    )
