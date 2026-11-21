from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# resolved placement intent must retain a named occurrence and independently authored rigid child to parent frame
@DataClass(frozen=True, slots=True)
class OccurrenceIn:
    NameValue: str
    FrameValue: PlaneFrame

    # malformed occurrence names or untyped geometry must fail before any shared parent publication begins
    def __post_init__(self) -> None:
        if (
            not ReadStyleText(self.NameValue, "assembly occurrence name")
            or type(self.FrameValue) is not PlaneFrame
        ):
            raise ValueError(
                "ordinary occurrence requires explicit name and typed placement frame"
            )
