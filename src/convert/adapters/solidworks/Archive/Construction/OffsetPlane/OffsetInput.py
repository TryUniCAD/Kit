from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# an actual datum name and independent signed distance define the measured native plane mode
@DataClass(frozen=True, slots=True)
class OffsetInput:
    NameValue: str
    DistanceValue: float
    IsReversed: bool
    VersionValue: int

    # the native driver shares the ordinary positive length domain with other features
    def __post_init__(self) -> None:
        if not ReadStyleText(self.NameValue, "offset plane name"):
            raise ValueError("offset plane requires a nonempty name")
        if type(CastValue(object, self.IsReversed)) is not bool:
            raise TypeError("offset plane requires an explicit reversal")
        _ = BlindEndInput(self.DistanceValue, False, self.VersionValue)
