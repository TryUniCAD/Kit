from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Units.CheckLengthUnit import (
    CheckLengthUnit,
)
from convert.adapters.solidworks.Archive.Config.Units.UnitSchemas import KUnitRowClasses
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# reused tags bypass the runtime body callback so every row must prove its role
def CheckUnitRows(RootValue: ArchiveNode, MapValue: ArchiveMaps) -> None:
    RowsValue = CastValue(list[dict[str, object]], RootValue.FieldsValue["items"])
    if len(RowsValue) != len(KUnitRowClasses):
        raise BodyUnsupported("SOLIDWORKS unit table has unsupported row owners")
    UnitValues: list[ArchiveNode] = []
    for RowValue, ClassValue in zip(RowsValue, KUnitRowClasses):
        UnitValue = RowValue["o"]
        if not isinstance(UnitValue, ArchiveNode) or UnitValue.ClassValue != ClassValue:
            raise BodyUnsupported("SOLIDWORKS unit table has unsupported row owners")
        IndexValue = ObjectIndex(MapValue, UnitValue)
        if IndexValue is None or IndexValue < MapValue.BaseValue:
            raise BodyUnsupported("SOLIDWORKS unit table reuses an earlier row")
        UnitValues.append(UnitValue)
    if UnitValues[3].FieldsValue["has_fb8"] != 0:
        raise BodyUnsupported(
            "SOLIDWORKS unit table has an unsupported density override"
        )
    CheckLengthUnit(UnitValues[0], MapValue)
