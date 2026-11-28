from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireRecord,
)


# selected stock cannot replace preexisting body outputs choices ghost state or an older atom manager
def CheckScopeFresh(CandidateValue: PartCandidate) -> dict[str, object]:
    ManagerValue = CandidateValue.SystemValue.RootValue.FieldsValue.get("fd88")
    if not isinstance(ManagerValue, dict):
        raise ValueError("selected stock requires a mutable actual atom manager")
    ManagerFields = CastValue(dict[str, object], ManagerValue)
    if (
        FieldInt(ManagerFields, "n6c") != 0
        or ReadRows(ManagerFields.get("atoms"))
        or FieldInt(ManagerFields, "fa8") != 0
    ):
        raise ValueError(
            "selected stock cannot replace a populated or older atom manager"
        )
    GhostFields = RequireRecord(
        CandidateValue.SystemValue.RootValue.FieldsValue.get("fd90")
    )
    if FieldInt(GhostFields, "n") != 0 or ReadRows(GhostFields.get("objects")):
        raise ValueError("selected stock cannot replace retained ghost bodies")
    CutValue = CandidateValue.CutValue
    if CutValue is None:
        raise ValueError("selected stock requires its actual fresh cut")
    for FeatureValue in (CandidateValue.BossValue.FeatureValue, CutValue.FeatureValue):
        FieldsValue = FeatureValue.FieldsValue
        if (
            any(
                FieldInt(FieldsValue, FieldName) != 0
                for FieldName in (
                    "f544",
                    "has_f528",
                    "has_f530",
                    "has_f548",
                    "has_f4a8",
                    "has_f4b0",
                    "has_f4c0",
                    "has_f4c8",
                    "n494",
                )
            )
            or FieldsValue["f538"] is not None
            or ReadRows(FieldsValue.get("f498"))
        ):
            raise ValueError(
                "selected stock cannot replace prior atom or scope ownership"
            )
    return ManagerFields
