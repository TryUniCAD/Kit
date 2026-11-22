from convert.adapters.solidworks.Archive.Construction.Styles.MakeAnnoData import (
    MakeAnnoData,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeCenterData(*, FontName: str) -> dict[str, object]:
    return {
        "f08": 0,
        "f10": 0.0,
        "f18": 1,
        "f20": 0.0,
        "f28": 0,
        "f2c": 0,
        "f30": 0,
        "f34": 0,
        "f38": 0,
        "f3c": 0,
        "f40": 1,
        "f44": 1,
        "f48": 1,
        "f4c": 0,
        "f78": 0.0,
        "f80": MakeAnnoData(FontName=FontName),
        "f148": 0,
    }
