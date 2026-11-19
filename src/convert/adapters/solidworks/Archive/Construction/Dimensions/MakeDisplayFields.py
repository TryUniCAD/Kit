from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeLineWidth import (
    MakeLineWidth,
)


# one display base constructs the actual shared native owners before a detail subtype adds its state
def MakeDisplayFields(VersionValue: int, FlagsValue: int) -> dict[str, object]:
    return {
        "f50": 0,
        "f30": None,
        "f40": None,
        "f48": None,
        "f54": 0,
        "f11c": 0,
        "f08": {
            "f00": 65535,
            "f02": 0,
            "f04": 3,
            "f08": {
                "f00": 4294967295,
                "f04": 0,
                "f08": MakeLineWidth(CategoryValue=0, WidthValue=-1.0),
            },
        },
        "f68": MakeObList(),
        "fb0": MakeObList(),
        "f58": 0,
        "ff8": None,
        "linked": 0,
        "f118": VersionValue,
        "f390": 0,
        "f3e0": FlagsValue,
        "f290": MakePoint(),
        "has_f298": 0,
        "has_f288": 0,
        "f3f8": None,
        "f400": MakePoint(),
        "f2a0": IdentityXform(),
        "has_f2c0": 0,
        "f2c8": 0.0,
        "has_f2d0": 0,
        "f2d8": None,
        "f3b8": -1.0,
        "f2f0": 1,
        "f2f8": MakeLineWidth(CategoryValue=0, WidthValue=-1.0),
        "f2f4": 0,
        "f304": 1,
        "f30c": MakeLineWidth(CategoryValue=0, WidthValue=-1.0),
        "f308": 0,
        "f300": 0,
        "f314": 0,
        "f334": -1,
        "f338": -1,
        "has_f4a0": 0,
        "f318": 1,
        "f31c": 0,
        "f320": MakeLineWidth(CategoryValue=0, WidthValue=-1.0),
        "f328": 0,
        "f32c": 0,
        "has_f4b8": 0,
    }
