from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Materials.CheckMatSlots import (
    CheckMatSlots,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# separate body material or density owners are outside the part assignment profile
def CheckMatAtoms(
    PartGraph: ConfigGraph, ConfigValue: ArchiveNode, ManagerValue: ArchiveNode
) -> None:
    PartFields = PartGraph.RootValue.FieldsValue
    ConfigFields = ConfigValue.FieldsValue
    AtomTable = NativeRecord(PartFields.get("fd88"))
    AtomRows = NativeRows(AtomTable.get("atoms"))
    BodyScene = NativeRecord(PartFields.get("f938"))
    if len(AtomRows) != 1 or AtomTable.get("n6c") != 1:
        raise BodyUnsupported(
            "SOLIDWORKS assigned material requires one actual solid atom"
        )
    AtomValue = RequireNative(AtomRows[0].get("o"), "moAtom_c")
    CheckMatSlots(PartGraph.MapValue, AtomValue)
    AtomId = AtomValue.FieldsValue.get("f140")
    AtomsValue = {
        EntryValue.EntryValue
        for EntryValue in PartGraph.MapValue.EntriesValue
        if isinstance(EntryValue.EntryValue, ArchiveNode)
        and EntryValue.EntryValue.ClassValue.NameValue == "moAtom_c"
    }
    if (
        AtomsValue != {AtomValue}
        or type(AtomId) is not int
        or AtomId <= 0
        or AtomValue.FieldsValue.get("body_kind") != 0
        or tuple(ConfigFields.get(NameValue) for NameValue in ("n420", "n430", "nb00"))
        != (0, 0, 1)
        or ConfigFields.get("fb00") != [{"a": AtomId, "b": 0}]
        or ManagerValue.FieldsValue.get("n600") != 0
        or tuple(BodyScene.get(NameValue) for NameValue in ("n08", "n58")) != (0, 0)
    ):
        raise BodyUnsupported(
            "SOLIDWORKS assigned material has an unqualified body or custom material override"
        )
