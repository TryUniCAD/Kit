from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitFields import (
    MakeUnitFields,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KLengthCodes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the pinned native dual unit getter creates the opposite metric or inch length owner from explicit constructor arguments without changing the primary format
def MakeDualLength(PrimaryUnit: str) -> ArchiveNode:
    if type(PrimaryUnit) is not str or PrimaryUnit not in KLengthCodes:
        raise ValueError(
            "dual length construction requires a recovered semantic length unit"
        )
    IsMetric = KLengthCodes[PrimaryUnit] in (0, 1, 2, 6, 7, 8)
    FieldsValue = MakeUnitFields(
        "length", KLengthCodes["in"] if IsMetric else KLengthCodes["mm"], 2
    )
    FieldsValue.update({"f10": int(IsMetric), "f18": 1.0, "f20": 1, "f28": 2})
    return ArchiveNode(RuntimeClass("moLengthUserUnits_c", 1), FieldsValue)
