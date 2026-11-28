from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckCylSpan import (
    CheckCylSpan,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.LocalCylShape import (
    LocalCylShape,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    PrismMeters,
    PrismVector,
)


# native carrier conventions must already describe the supplied portable parameterization
def CheckCylBasis(ShapeValue: LocalCylShape) -> None:
    MantleValue = ShapeValue.MantleValue
    AxisValue = PrismVector(MantleValue.axis)
    Radial = PrismVector(MantleValue.reference_direction)
    CheckCylSpan(
        PrismMeters(ShapeValue.NearRim.PlaneValue.origin),
        PrismMeters(ShapeValue.FarRim.PlaneValue.origin),
        AxisValue,
        Radial,
    )
    if PrismVector(ShapeValue.NearRim.PlaneValue.origin) != PrismVector(
        MantleValue.origin
    ):
        raise ValueError(
            "local cylinder axis origin must be its actual near cap station"
        )
    for RimValue, SignValue in ((ShapeValue.FarRim, 1), (ShapeValue.NearRim, -1)):
        PlaneValue = RimValue.PlaneValue
        CircleValue = RimValue.CircleValue
        if (
            PrismVector(PlaneValue.normal)
            != tuple(SignValue * Value for Value in AxisValue)
            or PrismVector(PlaneValue.reference_direction)
            != tuple(SignValue * Value for Value in Radial)
            or PrismVector(CircleValue.axis)
            != tuple(-SignValue * Value for Value in AxisValue)
            or PrismVector(CircleValue.reference_direction)
            != tuple(-SignValue * Value for Value in Radial)
            or PrismVector(CircleValue.center) != PrismVector(PlaneValue.origin)
            or CircleValue.radius != MantleValue.radius
        ):
            raise ValueError(
                "local cylinder cap or rim uses a noncanonical authored frame"
            )


# every owned source face curve edge and seam must appear in the supported two rims
def CheckCylSource(ShapeValue: LocalCylShape, TopologyValue: BrepTopology) -> None:
    FarRim, NearRim = ShapeValue.FarRim, ShapeValue.NearRim
    (ShellValue,) = TopologyValue.shells.values()
    if (
        tuple(
            TopologyValue.face_uses[UseId].face_id for UseId in ShellValue.face_use_ids
        )
        != (FarRim.CapFace.id, NearRim.CapFace.id, ShapeValue.SideFace.id)
        or {FarRim.PlaneValue.id, NearRim.PlaneValue.id, ShapeValue.MantleValue.id}
        != TopologyValue.surface_by_id.keys()
        or {FarRim.CircleValue.id, NearRim.CircleValue.id}
        != TopologyValue.curve_by_id.keys()
        or {FarRim.EdgeValue.id, NearRim.EdgeValue.id} != TopologyValue.edges.keys()
        or {FarRim.EdgeValue.start_vertex_id, NearRim.EdgeValue.start_vertex_id}
        != TopologyValue.vertex_by_id.keys()
    ):
        raise ValueError("local cylinder has unrepresented carriers or shell ownership")
    CheckCylBasis(ShapeValue)
