from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Mates.Distance.MakeDistInput import MakeDistInput
from tests.Convert.Solidworks.Research.Mates.Distance.RunSdkDistance import (
    RunSdkDistance,
)


# changing only the authored length must change its live mate parameter without modifying the generated child or other parent streams
def TestDistEdit() -> None:
    Before = RunSdkDistance(MakeDistInput("y", 0.071375))
    After = RunSdkDistance(MakeDistInput("y", 0.093625))
    assert Before["child"] == After["child"]
    FirstParent = CastValue(dict[str, object], Before["assembly"])
    SecondParent = CastValue(dict[str, object], After["assembly"])
    FirstStreams = CastValue(dict[str, object], FirstParent["streams"])
    SecondStreams = CastValue(dict[str, object], SecondParent["streams"])
    assert {
        NameValue
        for NameValue in FirstStreams
        if FirstStreams[NameValue] != SecondStreams[NameValue]
    } == {"Contents/Config-0-MatesList"}
    FirstValue = CastValue(dict[str, object], Before["readback"])
    SecondValue = CastValue(dict[str, object], After["readback"])
    assert (
        CastValue(dict[str, object], FirstValue["driving_distance"])["value_metres"]
        == 0.071375
    )
    assert (
        CastValue(dict[str, object], SecondValue["driving_distance"])["value_metres"]
        == 0.093625
    )
