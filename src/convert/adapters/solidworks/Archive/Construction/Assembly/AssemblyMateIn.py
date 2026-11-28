from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import (
    DistanceInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# complete assembly mating separates authored relationship intent from generated occurrences wrappers and persistent dimension allocation
@DataClass(frozen=True, slots=True)
class AssemblyMateIn:
    KindValue: str
    NameValue: str
    AxisValue: str
    FixedIndex: int
    DistanceValue: DistanceInput | None

    # the first complete profile admits exactly one aligned ordinary principal plane relationship and explicit positive driving distance when needed
    def __post_init__(self) -> None:
        if self.KindValue not in (
            "coincident",
            "parallel",
            "distance",
        ) or self.AxisValue not in ("x", "y", "z"):
            raise ValueError(
                "complete assembly requires a qualified ordinary planar mate"
            )
        if (
            not ReadStyleText(self.NameValue, "assembly mate name")
            or type(self.FixedIndex) is not int
            or self.FixedIndex not in (0, 1)
        ):
            raise ValueError(
                "assembly mate requires a name and one actual fixed occurrence index"
            )
        if (
            self.KindValue == "distance"
            and type(self.DistanceValue) is not DistanceInput
        ) or (self.KindValue != "distance" and self.DistanceValue is not None):
            raise ValueError(
                "driving distance intent must occur exactly on the distance mate branch"
            )
