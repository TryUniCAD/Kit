from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Units.BindCustomDensityMut import (
    BindDensityMut,
)
from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitNode import (
    MakeUnitNode,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KAngleCodes,
    KLengthCodes,
    KMassCodes,
    KSystemCodes,
    KUnitClasses,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the native sixteen class factory profile must be generated from explicit units rather than copied preferences
def MakeUnitTable(InputValue: UnitInput) -> ArchiveNode:
    if type(CastValue(object, InputValue)) is not UnitInput:
        raise TypeError("unit table construction requires validated semantic settings")
    CodesValue = {
        "length": KLengthCodes[InputValue.LengthUnit],
        "angle": KAngleCodes[InputValue.AngleUnit],
        "unit_system": KSystemCodes[InputValue.UnitSystem],
        "force": 2,
        "power": 0,
        "energy": 0,
        "time": 0,
    }
    UnitValues = {
        KindValue: MakeUnitNode(
            KindValue, CodesValue.get(KindValue), InputValue.DecimalPlaces
        )
        for KindValue in KUnitClasses
    }
    if InputValue.MassUnit is not None:
        BindDensityMut(
            UnitValues["density"],
            UnitValues["length"],
            KMassCodes[InputValue.MassUnit],
        )
    RowsValue = tuple({"o": UnitValue} for UnitValue in UnitValues.values())
    return ArchiveNode(
        RuntimeClass("moUnitsTable_c", 1), {"n": len(RowsValue), "items": RowsValue}
    )
