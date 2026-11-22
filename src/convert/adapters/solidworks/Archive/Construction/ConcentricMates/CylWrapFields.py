from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylPlace import (
    CylPlace,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# detached cylinders retain common constructor bounds until a real face enables its orientation state
def CylWrapFields(
    Component: ArchiveNode, PlaceValue: CylPlace, Radius: float
) -> dict[str, object]:
    return {
        "f58": Component,
        "f60": None,
        "f68": 1,
        "f6c": 0,
        "f08": 101,
        "has_f10": 0,
        "has_f18": 0,
        "f0c": -1,
        "f20": 0,
        "f74": -12345,
        "f78": -12345,
        "f7c": -12345,
        "f50": 0,
        "f70": 19000,
        "f34": 0,
        "f30": 0,
        "f98": 0,
        "f38": -1,
        "fb0": -1.0,
        "fb8": 1.0,
        "fc0": 1.0,
        "fc8": -1.0,
        "fd0": dict(zip("xyz", PlaceValue.OriginValue, strict=True)),
        "fe8": dict(zip("xyz", PlaceValue.WorldAxis, strict=True)),
        "f100": Radius,
        "has_f108": 0,
    }
