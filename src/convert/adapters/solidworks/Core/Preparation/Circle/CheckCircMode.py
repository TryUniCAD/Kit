from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from interchange.document.Models.DocumentModel import CadDocument


# circle admission must keep the measured support driver reversal and end profiles bound together
def CheckCircMode(DocumentValue: CadDocument, PlanValue: CirclePlan) -> None:
    EndValue = PlanValue.EndValue
    ProfileValue = (
        PlanValue.AxisValue,
        PlanValue.PlaneName,
        PlanValue.IsDiameter,
        EndValue.IsReversed,
        EndValue.ModeValue,
        EndValue.SecondDepth is not None,
    )
    if DocumentValue.units != "mm" or ProfileValue not in {
        ("z", "Front Plane", True, False, "blind", False),
        ("y", "Top Plane", False, True, "blind", False),
        ("x", "Right Plane", True, False, "mid_plane", False),
        ("y", "Top Plane", True, True, "two_directions", True),
    }:
        raise ValueError(
            "circle preparation is not qualified for this support driver or end profile"
        )
