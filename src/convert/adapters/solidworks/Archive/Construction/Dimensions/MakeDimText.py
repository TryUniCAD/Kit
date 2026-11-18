from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)


# planar mate distance initialization supplies native text kind eighteen after constructing independent empty text geometry and cache state
def MakeDimText() -> dict[str, object]:
    return {
        "n90": 0,
        "f98": [],
        "f08": "",
        "f38": MakePoint(),
        "f10": 18,
        "f18": None,
        "f20": 0,
        "f50": MakePoint(),
        "f68": 1.0,
        "fc4": 0,
        "fa0": 0,
        "fd0": 0,
        "fd8": 1e-6,
        "fe0": 1e-6,
        "f24": 0,
        "f0f0": MakeObList(),
        "f118": 0,
        "f120": 0,
        "f124": 0,
        "f128": 1.0,
        "f130": 0,
    }
