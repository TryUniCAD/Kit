from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from interchange.geometry.Models.SupportPlane import SupportPlane


# both stocks and the two plane hinge need their actual canonical model supports
def ReadPatPlanes(
    PlanesValue: Mapping[str, SupportPlane], AngledId: str
) -> tuple[SupportPlane, SupportPlane, SupportPlane, SupportPlane]:
    AngledPlane = PlanesValue.get(AngledId)
    FixedPlanes = {
        PlaneValue.name: PlaneValue
        for PlaneValue in PlanesValue.values()
        if PlaneValue.id != AngledId
    }
    NamesValue = ("Front Plane", "Top Plane", "Right Plane")
    if (
        AngledPlane is None
        or set(FixedPlanes) != set(NamesValue)
        or any(
            PlaneValue.support_selection_id is not None
            or PlaneValue.offset_parameter_id is not None
            for PlaneValue in FixedPlanes.values()
        )
    ):
        raise ValueError(
            "expected exactly unbound canonical Front Top and Right supports"
        )
    if any(
        ReadPrincAxis(FixedPlanes[NameValue].transform) != AxisValue
        for NameValue, AxisValue in zip(NamesValue, ("z", "y", "x"), strict=True)
    ):
        raise ValueError("fixed support name and actual frame disagree")
    return (
        FixedPlanes["Front Plane"],
        FixedPlanes["Top Plane"],
        FixedPlanes["Right Plane"],
        AngledPlane,
    )
