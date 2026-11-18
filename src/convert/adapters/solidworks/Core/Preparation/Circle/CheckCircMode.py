from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from interchange.document.Models.DocumentModel import CadDocument


# circle admission must keep each unqualified support driver and termination combination outside the initial public preparation boundary
def CheckCircMode(DocumentValue: CadDocument, PlanValue: CirclePlan) -> None:
    EndValue = PlanValue.EndValue
    ProfileValue = (
        PlanValue.AxisValue,
        PlanValue.PlaneName,
        PlanValue.IsDiameter,
        EndValue.IsReversed,
    )
    if (
        DocumentValue.units != "mm"
        or EndValue.ModeValue != "blind"
        or EndValue.SecondDepth is not None
        or ProfileValue
        not in {
            ("z", "Front Plane", True, False),
            ("y", "Top Plane", False, True),
        }
    ):
        raise ValueError(
            "circle preparation is not qualified for this support driver or end profile"
        )
