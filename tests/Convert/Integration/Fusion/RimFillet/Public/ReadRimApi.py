from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Integration.Fusion.RimFillet.Public.RimApiState import RimApiState


# source edit and restore measurements must remain separate from new offline geometry predictions
def ReadRimApi(CaseName: str, PhaseName: str = "initial") -> RimApiState:
    Entries = LoadJson(
        (
            FilePath(__file__).resolve().parents[6]
            / "re/Fusion/RimFilletPack/Qualification/Cases.json"
        ).read_text()
    )
    (Record,) = (Value for Value in Entries if Value["id"] == CaseName)
    State = Record["measurements"][PhaseName]
    (BodyValue,) = State["bodies"]
    return RimApiState(
        float(BodyValue["volume_cm3"]) * 1000,
        float(BodyValue["area_cm2"]) * 100,
        tuple(float(Value) * 10 for Value in BodyValue["centroid_cm"]),
        tuple(float(Value) * 10 for Value in BodyValue["min_cm"]),
        tuple(float(Value) * 10 for Value in BodyValue["max_cm"]),
        tuple(
            (str(Value["name"]), float(Value["value"])) for Value in State["parameters"]
        ),
    )
