from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionBook import (
    RevisionBook,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)


# nested revision owners require actual typed containment rather than a fabricated direct model backlink
def CheckLogParent(
    ModelValue: ArchiveNode, NodeValue: ArchiveNode, BookValue: RevisionBook
) -> None:
    KindValue = NodeValue.ClassValue.NameValue
    ParentValue = NodeValue.FieldsValue.get("owner")
    if KindValue not in (
        "moNotesAreaFtrFolder_c",
        "moAmbientLight_c",
        "moDirectionLight_c",
    ):
        if ParentValue is not ModelValue:
            raise ValueError("revision member has no actual part rooted owner")
        return
    if (
        not isinstance(ParentValue, ArchiveNode)
        or ParentValue.FieldsValue.get("owner") is not ModelValue
    ):
        raise ValueError("revision member has no actual part rooted owner")
    ExpectedKind = (
        "moDetailCabinet_c"
        if KindValue == "moNotesAreaFtrFolder_c"
        else "moEnvFolder_c"
    )
    if ParentValue.ClassValue.NameValue != ExpectedKind:
        raise ValueError("revision member has an unqualified containment path")
    ParentsValue = tuple(
        LogValue.OwnerValue
        for LogValue in BookValue.LogsValue
        if LogValue.OwnerValue.ClassValue.NameValue == ExpectedKind
    )
    if ParentsValue != (ParentValue,):
        raise ValueError("revision member owner must be the actual unique folder log")
    if (
        ExpectedKind == "moEnvFolder_c"
        and ModelValue.FieldsValue.get("f1e0") is not ParentValue
    ):
        raise ValueError(
            "revision light owner differs from the actual model environment"
        )
    if sum(ValueInput is NodeValue for ValueInput in ReadChildren(ParentValue)) != 1:
        raise ValueError(
            "revision member is absent or duplicated in its actual owner list"
        )
