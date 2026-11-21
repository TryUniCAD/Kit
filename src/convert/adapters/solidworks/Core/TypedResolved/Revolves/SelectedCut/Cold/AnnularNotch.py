from math import sin as Sin

from convert.Geometry.Revolve.OpenSweepWall import OpenSweepWall
from convert.Geometry.Revolve.PolygonSweep import BuildPolySweep
from convert.Geometry.Revolve.SweepFrame import RotateRadial
from convert.Geometry.Revolve.SweepMetrics import MeasureSweep
from convert.Geometry.Revolve.SweepVector import CrossVector, OffsetVector
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdSolid import (
    ColdSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.BuildRevBodyGeom import (
    BuildRevBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.MakeRevMerid import (
    MakeRevMeridian,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# a full annular stock has its centre on the directed axis at the mean height of its profile
def StockCentre(Owner: RevolveOwner) -> SpaceVector:
    Heights = tuple(Height for _, Height in MakeRevMeridian(Owner))
    Frame = Owner.FrameValue
    return OffsetVector(
        Frame.StartValue, Frame.DirectionValue, (min(Heights) + max(Heights)) / 2
    )


# the removed sector centroid uses cylindrical first moments in the same signed frame as the boundary
def NotchCentre(
    Frame: Transform,
    Radii: tuple[float, float],
    Heights: tuple[float, float],
    Interval: tuple[float, float],
) -> SpaceVector:
    Lower, Upper = Radii
    HalfAngle = (Interval[1] - Interval[0]) / 2
    RadialMoment = (2 / 3) * (Upper**2 + Upper * Lower + Lower**2) / (Upper + Lower)
    Direction = RotateRadial(Frame, (Interval[0] + Interval[1]) / 2)
    OnAxis = OffsetVector(Frame.origin, Frame.z_axis, sum(Heights) / 2)
    return OffsetVector(OnAxis, Direction, RadialMoment * Sin(HalfAngle) / HalfAngle)


# one clipped annular tool opens the selected wall and subtracts its volume and first moments from that stock
def BuildAnnularNotch(
    Stock: RevolveOwner, Cut: RevolveOwner, BodyId: str, SelectedIndex: int
) -> ColdSolid:
    Axis = Stock.FrameValue
    Direction = Axis.DirectionValue
    Radial = Axis.SupportValue.x_axis
    Origin = Axis.StartValue
    Full = BuildRevBody(Stock, BodyId)
    StockProfile = MakeRevMeridian(Stock)
    ToolProfile = MakeRevMeridian(Cut)
    StockRadii = tuple(Radius for Radius, _ in StockProfile)
    ToolRadii = tuple(Radius for Radius, _ in ToolProfile)
    Sign = -1 if Cut.IsReverse else 1
    ToolHeights = tuple(Sign * Height for _, Height in ToolProfile)
    Lower = max(min(StockRadii), min(ToolRadii))
    Upper = min(max(StockRadii), max(ToolRadii))
    Bottom, Top = min(ToolHeights), max(ToolHeights)
    Opening = (Upper, Lower)[SelectedIndex]
    Profile = ((Lower, Bottom), (Upper, Bottom), (Upper, Top), (Lower, Top))
    Angle = Cut.AngleValue.RadiansValue
    Interval = (-Angle, 0.0) if Cut.IsReverse else (0.0, Angle)
    Sector = BuildPolySweep(
        f"{BodyId}-notch", Profile, Origin, Direction, Radial, *Interval
    )
    Brep = OpenSweepWall(BodyId, Full.BrepValue, Sector, Opening)
    RemovedVolume, SectorArea, _ = MeasureSweep(
        Profile, Origin, Direction, Radial, *Interval
    )
    StockVolume = Full.TopologyValue.volume
    StockArea = Full.TopologyValue.surface_area
    Bounds = Full.TopologyValue.bounding_box
    if StockVolume is None or StockArea is None or Bounds is None:
        raise ValueError("full revolve stock lacks its analytic measures")
    Volume = StockVolume - RemovedVolume
    Area = StockArea + SectorArea - 2 * Angle * Opening * (Top - Bottom)
    if Volume <= 0.0 or Area <= 0.0:
        raise ValueError("selected revolve notch did not retain a solid")
    StockCenter = StockCentre(Stock)
    Frame = Transform(Origin, Radial, CrossVector(Direction, Radial), Direction)
    RemovedCenter = NotchCentre(Frame, (Lower, Upper), (Bottom, Top), Interval)
    Center = OffsetVector(
        StockCenter,
        SpaceVector(
            StockCenter.x - RemovedCenter.x,
            StockCenter.y - RemovedCenter.y,
            StockCenter.z - RemovedCenter.z,
        ),
        RemovedVolume / Volume,
    )
    return ColdSolid(Brep, Volume, Area, Bounds, Center)
