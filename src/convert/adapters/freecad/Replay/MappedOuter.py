from __future__ import annotations

from collections.abc import Callable, Mapping

from convert.adapters.freecad.Replay.MetadataTypes import IsPayloadMap, IsPayloadSeq
from interchange.Core.Common import FreezeMapping as FrozenMapping
from interchange.document.Models.DocumentModel import CadDocument


# this definition exists because focused behavior needs one stable owner
def MappedOuter(
    MetaValue: Mapping[str, object],
    Transform: Callable[[CadDocument], CadDocument] | None = None,
    *,
    ByReference: Mapping[str, Callable[[CadDocument], CadDocument]] | None = None,
) -> Mapping[str, object]:
    Freecad = MetaValue.get("freecad", {})
    if not IsPayloadMap(Freecad):
        return MetaValue
    Values = Freecad.get("external_documents", [])
    if not IsPayloadSeq(Values):
        return MetaValue
    Changed = False
    Mapped: list[object] = []
    for Value in Values:
        if not IsPayloadMap(Value):
            Mapped.append(Value)
            continue
        Linked = Value.get("document")
        MapValue = (
            Transform
            if ByReference is None
            else ByReference.get(str(Value.get("file", "")))
        )
        if MapValue is None or not isinstance(Linked, CadDocument):
            Mapped.append(Value)
            continue
        ItemValue = dict(Value)
        ItemValue["document"] = MapValue(Linked)
        Mapped.append(ItemValue)
        Changed = True
    if not Changed:
        return MetaValue
    FreecadCopy = dict(Freecad)
    FreecadCopy["external_documents"] = Mapped
    Result = dict(MetaValue)
    Result["freecad"] = FreecadCopy
    return FrozenMapping(Result)
