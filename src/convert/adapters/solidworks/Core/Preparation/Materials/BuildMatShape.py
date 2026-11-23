from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireBossDef import (
    RequireBossDef,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.BuildColdBox import (
    BuildColdBox,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.Records.RecordTopology import TopologyCounts


# the active blind depth and ordered rectangle provide an independently derived solid and exact counts
def BuildMatShape(DocumentValue: CadDocument) -> tuple[BrepModel, TopologyCounts]:
    (SketchValue,) = DocumentValue.sketches
    (PlaneValue,) = DocumentValue.support_planes
    (FeatureValue,) = DocumentValue.feature_timeline
    (BodyValue,) = DocumentValue.bodies
    Lines = tuple(
        Entity.geometry
        for Entity in SketchValue.entities
        if type(Entity.geometry) is LineGeometry and not Entity.construction
    )
    if len(Lines) != 4 or len(SketchValue.entities) != 4:
        raise ValueError("cold material solid requires the four actual contour edges")
    Depth = ReadLength(RequireBossDef(FeatureValue).length) * 1000.0
    Solid = BuildColdBox(
        PrismPlan(PlaneValue.transform, Lines, Depth, {}), BodyValue.id
    )
    BrepValue = Solid.BrepValue
    if BrepValue.validate(frozenset((BodyValue.id,))):
        raise ValueError("cold material shape did not produce a valid linked solid")
    return BrepValue, TopologyCounts(
        solid_count=1,
        shell_count=len(BrepValue.shells),
        face_count=len(BrepValue.faces),
        edge_count=len(BrepValue.edges),
        vertex_count=len(BrepValue.vertices),
        volume=Solid.VolumeValue,
        surface_area=Solid.AreaValue,
        bounding_box=Solid.BoundsValue,
        valid=True,
    )
