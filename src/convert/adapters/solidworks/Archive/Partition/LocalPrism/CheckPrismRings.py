from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFaceLoop import (
    PrismFaceLoop,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadFaceRing import (
    KPrismRing,
    ReadFaceRing,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadPrismFaces import (
    ReadPrismFaces,
)
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Parasolid import BrepTopology
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector


# a cyclic comparison preserves direction while allowing different loop starting vertices
def RotatePrismRing(RingValue: KPrismRing) -> KPrismRing:
    StartIndex = RingValue.index(min(RingValue))
    return RingValue[StartIndex:] + RingValue[:StartIndex]


# comparison uses exact geometric rings rather than copied plane parameterizations
def PrismRings(
    FacesValue: tuple[PrismFaceLoop, ...], TopologyValue: BrepTopology
) -> tuple[KPrismRing, ...]:
    ResultValues: list[KPrismRing] = []
    for BoundaryValue in FacesValue:
        PlaneValue = TopologyValue.surface_by_id[BoundaryValue.FaceValue.surface_id]
        if not isinstance(PlaneValue, PlaneSurface):
            raise ValueError("local prism face requires a plane carrier")
        ResultValues.append(ReadFaceRing(BoundaryValue, PlaneValue, TopologyValue))
    return tuple(ResultValues)


# a regenerated neutral prism proves the supplied complete rings occupy exactly one extrusion
def CheckPrismRings(
    FacesValue: tuple[PrismFaceLoop, ...], TopologyValue: BrepTopology
) -> None:
    RingsValue = PrismRings(FacesValue, TopologyValue)
    Levels = sorted(
        {VertexValue.point.z for VertexValue in TopologyValue.vertex_by_id.values()}
    )
    if len(Levels) != 2:
        raise ValueError("local prism requires two parallel XY section levels")
    Lower, Upper = Levels
    CapsValue = tuple(
        RingValue
        for RingValue in RingsValue
        if all(PointValue[2] == Lower for PointValue in RingValue)
    )
    if len(CapsValue) != 1:
        raise ValueError("local prism requires one lower section")
    Section = tuple(PlaneVector(XValue, YValue) for XValue, YValue, _ in CapsValue[0])
    LineValues = tuple(
        LineGeometry(StartValue, EndValue)
        for StartValue, EndValue in zip(Section, Section[1:] + Section[:1], strict=True)
    )
    Witness, _, _, _ = BuildPrism(
        "local-prism", KTransformIdentity, LineValues, Lower, Upper
    )
    WitnessTopology = BrepTopology(Witness)
    ExpectedRings = PrismRings(
        ReadPrismFaces(Witness, WitnessTopology), WitnessTopology
    )
    if sorted(map(RotatePrismRing, RingsValue)) != sorted(
        map(RotatePrismRing, ExpectedRings)
    ):
        raise ValueError(
            "local boundary does not form the exact prism of its lower section"
        )
