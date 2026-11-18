from dataclasses import dataclass as DataClass
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.PlaneEndIn import (
    PlaneEndIn,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import (
    DistanceInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# ordered planar group intent must preserve explicit endpoint ownership and positive driving length independently from generated graph identity
@DataClass(frozen=True, slots=True)
class GroupMateIn:
    KindValue: str
    NameValue: str
    EndValues: tuple[PlaneEndIn, PlaneEndIn]
    DistanceValue: DistanceInput | None

    # aligned kinds retain their shared datum guard while perpendicular preserves both actual principal selections without a scalar dimension
    def __post_init__(self) -> None:
        if self.KindValue not in (
            "coincident",
            "parallel",
            "distance",
            "perpendicular",
        ) or not ReadStyleText(self.NameValue, "planar group mate name"):
            raise ValueError(
                "planar groups require named qualified ordinary mate kinds"
            )
        if (
            type(self.EndValues) is not tuple
            or len(CastValue(tuple[object, ...], self.EndValues)) != 2
            or any(type(Value) is not PlaneEndIn for Value in self.EndValues)
        ):
            raise ValueError(
                "a planar mate requires two explicitly owned principal endpoints"
            )
        First, Second = self.EndValues
        if First.OccurrenceIndex == Second.OccurrenceIndex or (
            self.KindValue != "perpendicular" and First.AxisValue != Second.AxisValue
        ):
            raise ValueError(
                "the measured group profile requires distinct occurrences and the same principal datum axis"
            )
        if (
            self.KindValue == "distance"
            and type(self.DistanceValue) is not DistanceInput
        ) or (self.KindValue != "distance" and self.DistanceValue is not None):
            raise ValueError(
                "a positive driving dimension belongs exactly to a distance mate"
            )
