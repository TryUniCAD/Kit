from math import hypot as HypotValue, pi as PiValue, sqrt as SquareRoot

from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Records.RecordTopology import TopologyCounts
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.GeometryConics import EllipseGeometry
from interchange.geometry.Models.VectorSpace import SpaceVector


# the complete elliptic integral of the second kind converges by arithmetic and geometric means
def EllipPerim(MajorMm: float, MinorMm: float) -> float:
    Arithmetic, Geometric = 1.0, MinorMm / MajorMm
    Weight = 1.0
    Correction = (1.0 - Geometric * Geometric) * 0.5
    while Arithmetic - Geometric > 8e-16:
        HalfGap = (Arithmetic - Geometric) * 0.5
        Correction += Weight * HalfGap * HalfGap
        Arithmetic, Geometric = (Arithmetic + Geometric) * 0.5, SquareRoot(
            Arithmetic * Geometric
        )
        Weight *= 2.0
    return 2.0 * PiValue * MajorMm * (1.0 - Correction) / Arithmetic


# principal axis projection gives exact support extrema for a signed planar ellipse
def EllipMeasures(
    Ellipse: EllipseGeometry, HeightMm: float, Model: BrepModel
) -> TopologyCounts:
    RadiusA, RadiusB = Ellipse.major_radius, Ellipse.minor_radius
    Center, Major = Ellipse.center, Ellipse.major_axis
    ExtentX = HypotValue(RadiusA * Major.x, RadiusB * Major.y)
    ExtentY = HypotValue(RadiusA * Major.y, RadiusB * Major.x)
    CapArea = PiValue * RadiusA * RadiusB
    return TopologyCounts(
        solid_count=len(Model.bodies),
        shell_count=len(Model.shells),
        face_count=len(Model.faces),
        edge_count=len(Model.edges),
        vertex_count=len(Model.vertices),
        volume=CapArea * HeightMm,
        surface_area=2.0 * CapArea + EllipPerim(RadiusA, RadiusB) * HeightMm,
        bounding_box=BoundingBox(
            SpaceVector(Center.x - ExtentX, Center.y - ExtentY, 0.0),
            SpaceVector(Center.x + ExtentX, Center.y + ExtentY, HeightMm),
        ),
        valid=True,
    )
