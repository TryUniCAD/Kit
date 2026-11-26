from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Atoms.AtomTypes import KAtomClass
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the native manager indexes each distinct atom by its signed identifier
def CheckAtomMgr(Fields: dict[str, object], MapValue: ArchiveMaps) -> None:
    AtomRows = CastValue(list[dict[str, object]], Fields.get("atoms", []))
    if Fields["n6c"] != len(AtomRows):
        raise BodyUnsupported("unqualified SOLIDWORKS atom manager count")
    Identifiers: set[int] = set()
    for RowValue in AtomRows:
        NodeValue = RowValue["o"]
        if not isinstance(NodeValue, ArchiveNode) or NodeValue.ClassValue != KAtomClass:
            raise BodyUnsupported("SOLIDWORKS atom manager requires concrete atoms")
        SlotValue = ObjectIndex(MapValue, NodeValue)
        if SlotValue is None or SlotValue < MapValue.BaseValue:
            raise BodyUnsupported("SOLIDWORKS atom manager requires newly read atoms")
        AtomId = CastValue(int, NodeValue.FieldsValue["f140"])
        if AtomId in Identifiers:
            raise BodyUnsupported("duplicate SOLIDWORKS manager atom identifier")
        Identifiers.add(AtomId)
