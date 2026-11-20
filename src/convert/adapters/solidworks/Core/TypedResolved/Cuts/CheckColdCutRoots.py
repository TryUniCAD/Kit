from collections import Counter
from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemFolders,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# an empty atom manager can imply a single producer only with the complete ordinary root inventory
def CheckColdRoots(Features: Mapping[int, ArchiveNode]) -> None:
    Expected = dict.fromkeys(
        KSystemFolders
        | {"moDetailCabinet_c", "moOriginProfileFeature_c", "moExtrusion_c", "moICE_c"},
        1,
    )
    Expected.update(moProfileFeature_c=2, moRefPlane_c=3)
    Actual = Counter(NodeValue.ClassValue.NameValue for NodeValue in Features.values())
    if Actual != Expected:
        raise ValueError(
            "cold cut requires the whole ordinary pocket feature inventory"
        )
    if any(
        NodeValue.FieldsValue.get("f0c") not in (0, 1)
        or NodeValue.FieldsValue.get("f2c") != 0
        or NodeValue.FieldsValue.get("f2b0") != 19000
        or NodeValue.FieldsValue.get("has_list68") != 0
        or NodeValue.FieldsValue.get("f78") is not None
        for NodeValue in Features.values()
    ):
        raise ValueError("cold cut has alternate root or feature state")
