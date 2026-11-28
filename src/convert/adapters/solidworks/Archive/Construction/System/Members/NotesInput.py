from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# paired note captions and independent creation instants remain explicit source intentions
@DataClass(frozen=True, slots=True)
class NotesInput:
    HeadName: str
    EndName: str
    HeadCreated: FeatureInstant
    EndCreated: FeatureInstant

    # ambiguous names or unrepresented clock state must fail before partner allocation
    def __post_init__(self) -> None:
        if (
            any(
                not ReadStyleText(ValueInput, "notes folder identity")
                for ValueInput in (self.HeadName, self.EndName)
            )
            or self.HeadName == self.EndName
        ):
            raise ValueError("notes pair requires two distinct explicit captions")
        if not self.EndName.endswith("___EndTag___"):
            raise ValueError(
                "notes partner requires the mapped ordinary end tag vocabulary"
            )
        if (
            type(self.HeadCreated) is not FeatureInstant
            or type(self.EndCreated) is not FeatureInstant
        ):
            raise TypeError("notes pair requires two typed precise creation instants")
