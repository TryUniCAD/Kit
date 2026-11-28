from convert.adapters.Fusion.Measurement.IsFuseGeom import IsFuseGeom
from convert.adapters.Fusion.Measurement.ReadFuseMeas import (
    ReadMeasList,
    ReadMeasMap,
    ReadMeasNum,
)


# candidate and control states must contain a sound editable feature tree and measured solids
def ReadFuseState(Value: object) -> dict[str, object]:
    State = ReadMeasMap(Value)
    for ItemValue in ReadMeasList(State.get("features")):
        Feature = ReadMeasMap(ItemValue)
        Health = Feature.get("health")
        if type(Health) is not int or Health != 0 or Feature.get("message") != "":
            raise ValueError("Fusion measurement includes an unhealthy feature")
    for ItemValue in ReadMeasList(State.get("bodies")):
        BodyValue = ReadMeasMap(ItemValue)
        Center = ReadMeasList(BodyValue.get("center_mm"))
        if ReadMeasNum(BodyValue.get("volume_mm3")) <= 0 or len(Center) != 3:
            raise ValueError("Fusion measurement has invalid solid geometry")
        for Coordinate in Center:
            _ = ReadMeasNum(Coordinate)
    _ = ReadMeasList(State.get("parameters"))
    _ = ReadMeasList(State.get("sketches"))
    return State


# state identity preserves inventory rows while comparing native geometry numerically
def IsSameState(First: dict[str, object], Value: object) -> bool:
    Second = ReadFuseState(Value)
    return all(
        First[KeyText] == Second[KeyText]
        for KeyText in ("features", "sketches", "parameters")
    ) and IsFuseGeom(First["bodies"], Second["bodies"])
