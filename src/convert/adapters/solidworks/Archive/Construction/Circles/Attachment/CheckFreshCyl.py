from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)
from convert.adapters.solidworks.Container.Format import KPartitionStream


# preserving prior live owners requires a genuinely fresh single output and an empty body manager
def CheckFreshCyl(ChildValue: PartCandidate) -> dict[str, object]:
    RootValue = ChildValue.SystemValue.RootValue.FieldsValue
    Manager = RootValue["fd88"]
    if not isinstance(Manager, dict):
        raise ValueError(
            "concentric attachment requires the actual mutable body manager"
        )
    Manager = CastValue(dict[str, object], Manager)
    Feature = ChildValue.BossValue.FeatureValue.FieldsValue
    if (
        KPartitionStream in ChildValue.StreamsValue
        or ChildValue.CutValue is not None
        or ChildValue.SelfView is not None
        or ReadRows(Manager["atoms"])
        or any(FieldInt(Manager, NameValue) for NameValue in ("n6c", "fa8"))
        or ReadRows(RootValue["ffe0"])
        or RootValue.get("fe38") is not None
        or Feature.get("f538") is not None
        or any(
            FieldInt(Feature, NameValue)
            for NameValue in ("has_f528", "has_f530", "n494", "has_f3d0")
        )
    ):
        raise ValueError(
            "concentric attachment requires a fresh unused feature output and body manager"
        )
    return Manager
