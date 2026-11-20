from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the independent second producer shares the ice class with cutters but owns a separate operation
def BindExtrudeMut(
    FeatureValue: ArchiveNode,
    ProfileValue: ProfileGraph,
    EndValue: ArchiveNode,
    *,
    IndependentStock: bool = False,
) -> None:
    IsIce = FeatureValue.ClassValue.NameValue == "moICE_c"
    if IndependentStock and not IsIce:
        raise ValueError("independent stock mode requires an actual ICE feature")
    IsCut = IsIce and not IndependentStock
    CutFlags = (0x2 | 0x8 | 0x80 | 0x20000) if IsCut else 0
    FeatureValue.FieldsValue.update(
        {
            "f60": {
                "list": {"n": 1, "items": [{"o": ProfileValue.ProfileValue}]},
                "tail": 0,
            },
            "f28": CastValue(int, FeatureValue.FieldsValue["f28"]) | 0x140 | CutFlags,
            "f810": 1 if IsCut else 0 if IndependentStock else -1,
            "f818": EndValue,
            "f838": 0.0,
        }
    )
