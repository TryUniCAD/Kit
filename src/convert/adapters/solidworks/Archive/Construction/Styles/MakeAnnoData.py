from convert.adapters.solidworks.Archive.Construction.Styles.MakeHelperFont import (
    MakeHelperFont,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeAnnoData(*, FontName: str) -> dict[str, object]:
    return {
        "f08": MakeHelperFont(FontName=FontName),
        "f68": 3,
        "f6c": -1,
        "f70": 0,
        "f74": 0,
        "f78": 1,
        "f7c": 1,
        "f80": 0,
        "f88": 0.0,
        "f90": 0,
        "f94": 1,
        "f98": 0,
        "fa0": 0.0,
        "fa8": 0,
    }
