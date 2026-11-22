from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Config.Material.MatTypes import (
    KDensityClass,
    KMaterialClass,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# ordinary physical density belongs to a fresh unnamed parameter with one modeled metric value
def MakePartDensity(DensityValue: float) -> ArchiveNode:
    if (
        isinstance(DensityValue, bool)
        or not IsFinite(DensityValue)
        or DensityValue <= 0
    ):
        raise ValueError("part material density must be positive and finite")
    ParameterValue = ArchiveNode(
        KDensityClass,
        {
            "f18": None,
            "f0c": 0,
            "f28": 0x40000000,
            "f08": -1,
            "f2c": 0,
            "f20": "",
            "f48": None,
            "f58": float(DensityValue),
            "f68": 0,
        },
    )
    return ArchiveNode(KMaterialClass, {"f08": ParameterValue})
