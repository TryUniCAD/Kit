from math import pi as PiValue

from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from convert.Geometry.SweptTube.MakeTubeRim import MakeTubeRim
from interchange.brep.Surfaces.BrepSurfaces import TorusSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepFace
from interchange.geometry.Models.VectorSpace import SpaceVector


# the signed origin start quarter tube has two outward planar caps and one periodic torus wall
def BuildQuarter(BodyId: str, SectionRadius: float, PathRadius: float) -> BrepModel:
    Prefix = f"{BodyId}-quarter-tube"
    NegativeY = SpaceVector(0.0, -1.0, 0.0)
    StartRim = MakeTubeRim(
        f"{Prefix}-start",
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(-1.0, 0.0, 0.0),
        NegativeY,
        SectionRadius,
        0.0,
        1.0,
    )
    EndRim = MakeTubeRim(
        f"{Prefix}-end",
        SpaceVector(PathRadius, PathRadius, 0.0),
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(1.0, 0.0, 0.0),
        SectionRadius,
        PiValue / 2.0,
        -1.0,
    )
    TorusValue = TorusSurface(
        f"{Prefix}-torus",
        SpaceVector(0.0, PathRadius, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        NegativeY,
        PathRadius,
        SectionRadius,
    )
    WallValue = BrepFace(
        f"{Prefix}-wall",
        TorusValue.id,
        (StartRim.LoopValues[1].id, EndRim.LoopValues[1].id),
    )
    return BuildSweepModel(
        BodyId,
        Prefix,
        (StartRim.CurveValue, EndRim.CurveValue),
        (StartRim.CapValue, EndRim.CapValue, TorusValue),
        (StartRim.VertexValue, EndRim.VertexValue),
        (StartRim.EdgeValue, EndRim.EdgeValue),
        (StartRim.CapFace, EndRim.CapFace, WallValue),
        (*StartRim.LoopValues, *EndRim.LoopValues),
        (*StartRim.UseValues, *EndRim.UseValues),
        PcurvesValue=(*StartRim.PCurveValues, *EndRim.PCurveValues),
    )
