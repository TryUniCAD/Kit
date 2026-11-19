from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Drawing.Definition.Appearance.AppearanceState import (
    AppearanceState,
)


# empty managers still need explicit source presence and allocator history rather than saved field rows
@DataClass(frozen=True, slots=True)
class EmptyMgrInput:
    BomOnWire: bool
    AppearanceValue: AppearanceState

    # absent transmitted appearance state can only reconstruct the independently proven constructor seed
    def __post_init__(self) -> None:
        if type(CastValue(object, self.BomOnWire)) is not bool:
            raise TypeError("empty BOM presence requires an explicit boolean")
        if type(self.AppearanceValue) is not AppearanceState:
            raise TypeError("empty rendering manager requires typed appearance state")
        if (
            not self.AppearanceValue.ManagerOnWire
            and self.AppearanceValue.NextAppearanceId != 1
        ):
            raise ValueError(
                "absent appearance state cannot preserve a nondefault allocator"
            )
