from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.History.HistoryTypes import KDateHistClass
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a mapped reference can bypass the object body callback so its concrete role remains explicit
def CheckHistRefs(RootValue: ArchiveNode) -> None:
    if "states" not in RootValue.FieldsValue:
        raise BodyUnsupported("SOLIDWORKS version history requires states")
    StatesValue = ReadBodyRows(FieldScope(RootValue.FieldsValue), "states")
    if not StatesValue:
        raise BodyUnsupported("SOLIDWORKS version history requires states")
    for RowValue in StatesValue:
        if not isinstance(RowValue, Mapping):
            raise BodyUnsupported("SOLIDWORKS version history requires state rows")
        StateValue = CastValue(Mapping[str, object], RowValue).get("st")
        if not isinstance(StateValue, Mapping):
            raise BodyUnsupported("SOLIDWORKS version history requires state fields")
        DateValue = CastValue(Mapping[str, object], StateValue).get("f38")
        if (
            not isinstance(DateValue, ArchiveNode)
            or DateValue.ClassValue != KDateHistClass
        ):
            raise BodyUnsupported("SOLIDWORKS version state requires date code history")
