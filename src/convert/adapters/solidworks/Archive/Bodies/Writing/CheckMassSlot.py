from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.MassCacheFields import (
    KMassCacheFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.GeometryFields import (
    KGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.MassPropFields import (
    KMassPropFields,
)
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows


# cache members must belong to the slot before the shared writer can resolve inherited values
def CheckMassSlot(SlotScope: FieldScope) -> None:
    FieldsValue = SlotScope.FieldsValue
    if "f08" not in FieldsValue or set(FieldsValue) - {"n10", "f08", "f18"}:
        raise BodyUnsupported("SOLIDWORKS mass cache slot has unmodeled fields")
    AtomValues = ReadBodyRows(SlotScope, "f08")
    if bool(AtomValues) != ("f18" in FieldsValue):
        raise BodyUnsupported("SOLIDWORKS mass cache property requires atom rows")
    AtomNames = {RuleValue.NameValue for RuleValue in KMassCacheFields[1].BodyValue}
    if any(
        not isinstance(AtomValue, MutableMapping)
        or set(CastValue(MutableMapping[str, object], AtomValue)) != AtomNames
        for AtomValue in AtomValues
    ):
        raise BodyUnsupported("SOLIDWORKS mass cache atom row has unmodeled fields")
    if not AtomValues:
        return
    PropValue = FieldsValue["f18"]
    PropNames = {RuleValue.NameValue for RuleValue in KMassPropFields}
    if (
        not isinstance(PropValue, MutableMapping)
        or set(CastValue(MutableMapping[str, object], PropValue)) != PropNames
    ):
        raise BodyUnsupported("SOLIDWORKS mass cache property has unmodeled fields")
    PropFields = CastValue(MutableMapping[str, object], PropValue)
    for RuleValue in KMassPropFields:
        if RuleValue.KindValue != "Embed":
            continue
        VectorValue = PropFields[RuleValue.NameValue]
        VectorNames = {
            Entry.NameValue for Entry in KGeometryFields[RuleValue.TypeValue]
        }
        if (
            not isinstance(VectorValue, MutableMapping)
            or set(CastValue(MutableMapping[str, object], VectorValue)) != VectorNames
        ):
            raise BodyUnsupported("SOLIDWORKS mass cache vector has unmodeled fields")
