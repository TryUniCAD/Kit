from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Views.CheckRotation import CheckRotation
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# caller presentation needs a semantic contract independent of saved native object graphs
@DataClass(frozen=True, slots=True)
class ViewInput:
    MatrixValues: tuple[float, ...]
    ShiftValues: tuple[float, float, float]
    ScaleValue: float

    # invalid camera state must fail before any stream or container is generated
    def __post_init__(self) -> None:
        CheckRotation(self.MatrixValues)
        if (
            type(CastValue(object, self.ShiftValues)) is not tuple
            or len(self.ShiftValues) != 3
        ):
            raise ValueError(
                "view translation must contain three immutable coordinates"
            )
        object.__setattr__(
            self,
            "ShiftValues",
            tuple(RequireScalar(Value) for Value in self.ShiftValues),
        )
        if RequireScalar(self.ScaleValue) <= 0.0:
            raise ValueError("view scale must be positive")
