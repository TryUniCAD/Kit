from convert.adapters.solidworks.Archive.Construction.Styles.MakeAnnoData import (
    MakeAnnoData,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeTargetData(*, FontName: str) -> dict[str, object]:
    return {
        "f08": "",
        "f10": "",
        "f18": "",
        "f20": "",
        "f28": "",
        "f30": 0,
        "f34": 0,
        "f38": 0,
        "f3c": 1,
        "f40": 0,
        "f44": 0,
        "f48": 0,
        "f4c": 1,
        "f50": 0.03,
        "f58": 0.03,
        "f60": 0,
        "f68": 0.0,
        "f70": -1,
        "f74": 0,
        "f78": {"x": 0.0, "y": 0.0, "z": 0.0},
        "f90": 0,
        "fb0": 0,
        "fc0": MakeAnnoData(FontName=FontName),
    }
