from convert.adapters.solidworks.Archive.Construction.Styles.MakeAnnoData import (
    MakeAnnoData,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeGtolFrame import (
    MakeGtolFrame,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeHelperFont import (
    MakeHelperFont,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeGtolData(*, FontName: str) -> dict[str, object]:
    return {
        "n08": 2,
        "f08": [{"e": MakeGtolFrame()}, {"e": MakeGtolFrame()}],
        "f30": 1,
        "f34": 2,
        "f38": "",
        "f40": 0,
        "f44": 0,
        "f48": 0,
        "f4c": 1,
        "f50": 1,
        "f54": 0,
        "f58": 0,
        "f60": "",
        "f68": 0,
        "f70": "",
        "f78": "",
        "f80": 0,
        "f88": "",
        "f90": "",
        "f98": 0,
        "f9c": 0,
        "fa0": 0,
        "fa4": 0,
        "fa8": 0,
        "fac": 1,
        "fb0": MakeHelperFont(FontName=FontName),
        "f110": 0,
        "f114": 0,
        "f118": MakeAnnoData(FontName=FontName),
        "f1e0": 0,
    }
