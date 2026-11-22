from convert.adapters.solidworks.Archive.Construction.Model.ModelArrays import (
    KModelArrays,
    KModelLists,
)
from convert.adapters.solidworks.Archive.Construction.Model.ModelNulls import (
    KModelNulls,
)
from convert.adapters.solidworks.Archive.Construction.Model.ModelZeroes import (
    KModelZeroes,
)
from convert.adapters.solidworks.Archive.Construction.Model.PartZeroes import (
    KPartZeroes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# constructor neutral model collections exclude hidden bodies transforms shrinkwrap and shape modifiers before geometry is reconstructed
def CheckPrismRoot(RootValue: ArchiveNode, ColdAtom: ArchiveNode | None = None) -> None:
    Fields = RequireNative(RootValue, "moPart_c").FieldsValue
    if Fields.get("f2c") != 0x100 or any(
        Fields.get(FieldName) != 0 for FieldName in (*KModelZeroes, *KPartZeroes)
    ):
        raise ValueError("cache free prism has unqualified model mode flags")
    if any(
        Fields.get(FieldName) is not None
        for FieldName in KModelNulls
        if FieldName != "f1e0"
    ):
        raise ValueError("cache free prism has additional model attachments")
    for CountName, FieldName in KModelArrays:
        if Fields.get(CountName) != 0 or not IsLineState(Fields.get(FieldName)):
            raise ValueError(
                "cache free prism has populated model geometry collections"
            )
    for FieldName in (
        *KModelLists,
        "f938",
        "fdd0",
        "f1c70",
        "f60",
        "fa48",
        "fa50",
        "f9d8",
    ):
        if not IsLineState(Fields.get(FieldName)):
            raise ValueError("cache free prism has populated model owners")
    AtomsValue = NativeRecord(Fields.get("fd88"))
    GhostValue = NativeRecord(Fields.get("fd90"))
    if (
        AtomsValue.get("n6c") != (0 if ColdAtom is None else 1)
        or AtomsValue.get("fa8") != 0
        or (ColdAtom is None and AtomsValue.get("atoms"))
        or GhostValue.get("n") != 0
        or GhostValue.get("objects")
    ):
        raise ValueError("cache free prism has stored live or ghost bodies")
    if Fields.get("f1420") is not None or Fields.get("f13f8") is not None:
        raise ValueError("cache free prism has additional direct part owners")
