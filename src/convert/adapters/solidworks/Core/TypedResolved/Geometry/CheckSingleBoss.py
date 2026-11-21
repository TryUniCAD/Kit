from collections import Counter
from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemFolders,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# complete single boss history must exclude another solid producer or profile
def CheckSingleBoss(Features: Mapping[int, ArchiveNode], SolidClass: str) -> None:
    CountsValue = Counter(
        NodeValue.ClassValue.NameValue for NodeValue in Features.values()
    )
    Expected = dict.fromkeys(
        KSystemFolders
        | {
            "moDetailCabinet_c",
            "moOriginProfileFeature_c",
            "moProfileFeature_c",
            SolidClass,
        },
        1,
    )
    Expected["moRefPlane_c"] = 3
    if CountsValue != Expected:
        raise ValueError("SOLIDWORKS requires the whole ordinary single boss inventory")
