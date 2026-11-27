from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)


# distance displays retain their independent native subtype state after the common annotation and display constructor runs
def MakeDistTail() -> dict[str, object]:
    return {
        "f1014": 0,
        "ffb8": 0.0,
        "ffc0": 0.0,
        "ffe8": MakePoint(),
        "f1000": 0,
        "f1008": None,
        "f1010": 0,
    }
