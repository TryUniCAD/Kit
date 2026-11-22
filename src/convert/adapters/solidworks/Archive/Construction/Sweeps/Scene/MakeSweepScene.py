from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.MemberInput import (
    MemberInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import (
    NotesInput,
)


# the measured authored sweep scene uses a deterministic ambient and three orthogonal directional sources
def MakeSweepScene(WrittenAt: int) -> MemberInput:
    CreatedValue = FeatureInstant(WrittenAt, 0)
    AmbientValue = LightInput(
        "ambient",
        "Ambient",
        "SweepAmbient",
        0.5,
        0.5,
        0.0,
        0xFFFFFF,
        True,
        False,
        True,
        1.0,
        True,
        16.0,
        None,
        None,
        CreatedValue,
    )
    Directions = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    LightsValue = tuple(
        LightInput(
            "directional",
            f"Directional{Index}",
            f"SweepLight{Index}",
            0.0,
            0.5,
            0.25,
            0xFFFFFF,
            True,
            False,
            True,
            1.0,
            True,
            16.0,
            Direction,
            0.5,
            CreatedValue,
        )
        for Index, Direction in enumerate(Directions, 1)
    )
    NotesValue = NotesInput("Notes", "Notes1___EndTag___", CreatedValue, CreatedValue)
    return MemberInput(NotesValue, (AmbientValue, *LightsValue))
