from __future__ import annotations

from builtins import getattr as GetAttr
from types import ModuleType


def BuildRecords(
    InputData: dict[str, dict[str, object]],
    StyleModule: ModuleType,
    UnitsModule: ModuleType,
    CoreModule: ModuleType,
) -> list[object]:
    StyleData = GetAttr(StyleModule, "detail_definitions")(**InputData["styles"])
    UnitInput = InputData["units"]
    if "definitions" in UnitInput:
        UnitTable = GetAttr(UnitsModule, "units_table")(**UnitInput)
    else:
        UnitTable = GetAttr(UnitsModule, "unit_table_profile")(**UnitInput)
    return [GetAttr(CoreModule, "Obj")("moDetailDefs_c", StyleData), UnitTable]
