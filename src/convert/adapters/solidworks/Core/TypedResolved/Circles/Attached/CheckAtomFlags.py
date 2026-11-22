from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState


# a saved chooser differs from active body selection and has its own separate ownership validation
def CheckAtomFlags(BossValue: ArchiveNode, SavedBody: bool) -> None:
    Fields = BossValue.FieldsValue
    Expected = {"has_f528": 1, "n494": 1, "f540": 3, "has_f3d0": 1}
    if SavedBody:
        Expected.update(has_f4a8=1, has_f4b0=1, f4b8=1, has_f4c0=1)
    if (
        any(
            Fields.get(NameValue) != Expected.get(NameValue, 0)
            for NameValue in KAtomWords
        )
        or any(
            not IsLineState(Fields.get(NameValue))
            for NameValue in KAtomLists
            if NameValue != "f498"
        )
        or any(Fields.get(NameValue) != 0 for NameValue in ("f3c0", "f3c8", "f580"))
        or Fields.get("f4a0") != 1
    ):
        raise ValueError("SOLIDWORKS attached circle has unsupported output ownership")
