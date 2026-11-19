from collections.abc import Sized
from struct import pack as PackValues
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDisplayFields import (
    MakeDisplayFields,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeFavorite import (
    MakeFavorite,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeRawIdentity import (
    MakeRawIdentity,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeTextFields import (
    MakeTextFields,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.RequireDisplay import (
    RequireDisplay,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
)


# native distance and angle displays share one constructor while their text kinds subtype tails and document style remain separately owned
def MakeCommonView(
    HandleValue: ArchiveNode, DesignIntent: bool, SelectedLeader: int, TextKind: int
) -> dict[str, object]:
    OwnerValue = RequireDisplay(HandleValue, DesignIntent, SelectedLeader, TextKind)
    FieldsValue: dict[str, object] = {
        **MakeDisplayFields(FieldInt(OwnerValue.FieldsValue, "f2b0"), 524416),
        "f6a0": MakeTextFields(TextKind),
        "f870": 1,
        "f874": 1,
        "f878": 0,
        "f7f8": "",
        "f800": "",
        "f818": "",
        "f820": "",
        "f880": MakePoint(XValue=1.0),
        "f8a8": 0.5,
        "f8b0": 0.0,
        "f950": 0.0,
        "fa78": -1.0,
        "f958": MakePoint(),
        "f970": MakePoint(),
        "f988": MakePoint(),
        "f9a0": MakePoint(),
        "f9b8": MakePoint(),
        "has_fa50": 0,
        "f898": 0,
        "f89c": 0,
        "f8a0": 0,
        "f8c0": 5,
        "f8e4": 2,
        "f8ec": 2,
        "f8f4": 2,
        "fa38": MakePoint(),
        "f580": None,
        "f588": None,
        "f5a0": 0.0,
        "f5a8": 0.0,
        "has_f590": 0,
        "has_f598": 0,
        "f8e8": 2,
        "f8f0": 2,
        "f8a4": 1063 | 2147483648,
        "has_fa58": 0,
        "has_fa60": 0,
        "fa70": "",
        "faf8": None,
        "fb00": None,
        "f8f8": -1,
        "fad0": 0.0,
        "f5b0": {
            "elem": 8,
            "alloc_a": 16,
            "alloc_b": 1,
            "n": 1,
            "data": PackValues("<d", 0.0),
        },
        "f680": "",
        "f688": MakeFavorite(),
        "fb40": -1.0,
        "fb68": 4,
        "fb6c": 65535,
        "fb60": (252 | 131073 | (256 if DesignIntent else 0)) & 4261412863 | 3772792832,
        "f830": 0.0,
        "f838": 0.0,
        "f840": 0.0,
        "f848": 0.0,
        "faf4": 0,
        "f8b8": -25.0,
        "f8fc": 1,
        "f900": 0,
        "f5c0": MakeRawIdentity(),
        "f648": 1.0,
        "fb70": "",
        "fb78": "",
        "fb80": "",
        "fb88": "",
        "fe48": MakeObList(),
        "f908": MakeObList(),
        "fb9c": -1,
        "fe40": 0,
        "fa80": None,
        "fa88": None,
        "fba0": None,
        "fb64": 6256 & 4294967031 | 524805 | 196608 | 278528,
        "fab0": None,
        "fab8": None,
        "has_fac0": 0,
        "has_fac8": 0,
        "fa90": 0,
        "fef8": None,
        "fb4c": 1,
        "fb50": 1,
        "fd78": 0,
        "fd7c": 0,
        "ff00": 0,
        "f8c8": 0.0,
        "f8d0": 0,
        "ff08": 0,
        "ff0c": 0,
        "ff10": 0,
        "f8d8": 0,
        "f8dc": 0,
        "f808": "",
        "f810": "",
        "fd80": -1,
        "ff84": 0,
        "ff54": 0,
        "ff60": "",
        "f650": 0,
        "ff80": SelectedLeader,
        "ff68": MakePoint(),
        "ff58": 0,
        "f8e0": 0,
        "ff88": "",
    }
    Collections = {
        "n2b0": "f2b0",
        "n3d0": "f3c0",
        "n2e8": "f2e0",
        "n4a8": "f4a8",
        "n4f0": "f4f0",
        "n550": "f550",
        "n850": "f850",
    }
    for ListName in Collections.values():
        FieldsValue[ListName] = []
    FieldsValue["f4f0"] = tuple({"p": MakePoint()} for _ in range(4))
    FieldsValue["f550"] = tuple({"v": MakePoint(YValue=1.0)} for _ in range(2))
    FieldsValue["f850"] = ({"o": HandleValue},)
    for CountName, ListName in Collections.items():
        FieldsValue[CountName] = len(CastValue(Sized, FieldsValue[ListName]))
    return FieldsValue
