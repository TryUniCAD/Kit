from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitFields import (
    MakeUnitFields,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KUnitClasses,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# unit table rows require distinct concrete archive identities while embedded style formats use the same field rules
def MakeUnitNode(
    KindValue: str, UnitCode: int | None, DecimalPlaces: int
) -> ArchiveNode:
    FieldsValue = MakeUnitFields(KindValue, UnitCode, DecimalPlaces)
    return ArchiveNode(RuntimeClass(KUnitClasses[KindValue], 1), FieldsValue)
