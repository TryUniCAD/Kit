from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)


# each inherited dormant original dimension holder needs its own native constructor state
def MakePatOrig() -> dict[str, object]:
    return {
        "f00": 1,
        "f08": None,
        "has_f10": 0,
        "f18": 0,
        "f20": 0.0,
        "fb4": 0,
        "fb8": 0.0,
        "fc0": 0.0,
        "f260": 0,
        "fc8": -1,
        "fcc": -1,
        "fd0": 0,
        "fd4": 0,
        "f1d8": 0,
        "f1d0": 0,
        "f1d4": 0,
        "f218": -1,
        "has_f228": 0,
        "n1e0": 0,
        "f1e0": [],
        "f1c0": 0,
        "f1b0": MakeObList(),
        "f25c": 0,
    }
