from convert.adapters.solidworks.Archive.Construction.Circles.CircleModes import (
    KMeasCircModes,
    KOrdCircModes,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from interchange.document.Models.DocumentModel import CadDocument


# circle admission binds the actual canonical support and all active end owners
def CheckCircMode(
    DocumentValue: CadDocument, PlanValue: CirclePlan, *, Measured: bool = False
) -> None:
    EndValue = PlanValue.EndValue
    ProfileValue = (
        PlanValue.AxisValue,
        PlanValue.IsDiameter,
        EndValue.IsReversed,
        EndValue.ModeValue,
        EndValue.SecondDepth is not None,
    )
    PlaneNames = {"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"}
    ModesValue = KMeasCircModes if Measured else KOrdCircModes
    if (
        DocumentValue.units != "mm"
        or PlaneNames.get(PlanValue.AxisValue) != PlanValue.PlaneName
        or ProfileValue not in ModesValue
    ):
        raise ValueError(
            "circle preparation is not qualified for this support driver or end profile"
        )
