from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.EndMode import KEndMode
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature


# active neutral terminations and directions must map to the distinct measured solid boss end roles
def ReadBossEnd(Definition: ExtrudeFeature, AxisValue: str) -> BossEndInput:
    ModesValue: dict[ExtrudeEnd | str, KEndMode] = {
        ExtrudeEnd.KBlind: "blind",
        ExtrudeEnd.KMidPlane: "mid_plane",
        ExtrudeEnd.KTwoLengths: "two_directions",
    }
    ModeValue = ModesValue.get(Definition.end_condition)
    if ModeValue is None or Definition.symmetric != (ModeValue == "mid_plane"):
        raise ValueError("ordinary boss end condition and symmetric intent disagree")
    if (
        Definition.direction is not None
        and (
            Definition.direction.x,
            Definition.direction.y,
            Definition.direction.z,
        )
        != PrincipalFrame(AxisValue).NormalValue
    ):
        raise ValueError("ordinary boss direction must use the actual support normal")
    SecondValue = Definition.second_length
    if ModeValue == "two_directions":
        if SecondValue is None or Definition.second_end_condition != ExtrudeEnd.KBlind:
            raise ValueError(
                "two direction boss requires its independent blind second end"
            )
    elif SecondValue is not None or Definition.second_end_condition is not None:
        raise ValueError("single ended boss cannot carry a second active end")
    return BossEndInput(
        ReadLength(Definition.length),
        Definition.reversed,
        19000,
        ModeValue,
        None if SecondValue is None else ReadLength(SecondValue),
    )
