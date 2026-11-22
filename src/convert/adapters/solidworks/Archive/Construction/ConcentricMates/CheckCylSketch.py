from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# the generated circle and its actual fixed centre must have the requested live radial role
def CheckCylSketch(
    ChildValue: PartCandidate, LinkValue: NativeLink, ArcMarker: int
) -> None:
    PlanValue = ChildValue.PlanValue
    Profile = ChildValue.ProfileValue
    Geometry = Profile.GeometryValue
    if not isinstance(PlanValue, CirclePlan) or not isinstance(Geometry, CircleGraph):
        raise ValueError("concentric child lacks its actual generated circle")
    ArcValue = Geometry.ArcValue.FieldsValue
    Observed = ReadLocalCirc(Geometry.SketchValue, LinkValue)
    if (
        Profile.ProfileValue.FieldsValue.get("pd_f80") is not Geometry.SketchValue
        or ArcValue.get("_center") is not Geometry.CenterValue
        or ArcValue.get("_start") is not Geometry.MarkerValue
        or ArcValue.get("_end") is not Geometry.MarkerValue
        or FieldInt(ArcValue, "f08") != ArcMarker
        or Observed is None
        or Observed[1] is None
    ):
        raise ValueError("concentric child lost its actual centre arc or radial driver")
    LocalValue, _ = Observed
    if LocalValue.ModeValue != (
        "diameter" if PlanValue.IsDiameter else "radius"
    ) or not IsClose(
        LocalValue.RadiusValue,
        PlanValue.CircleValue.RadiusValue * 1e3,
        rel_tol=1e-12,
        abs_tol=1e-10,
    ):
        raise ValueError(
            "concentric child radial driver disagrees with its authored circle"
        )
