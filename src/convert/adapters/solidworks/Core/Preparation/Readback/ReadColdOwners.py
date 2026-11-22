from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# regeneration needs the linked boss and the datum of its actual sketch
def ReadColdOwners(
    Document: CadDocument, SketchValue: Sketch, Driver: Parameter
) -> tuple[FeatureStep, SupportPlane]:
    Owners = tuple(
        ItemValue
        for ItemValue in Document.feature_timeline
        if ItemValue.id == Driver.owner_id
    )
    Planes = tuple(
        ItemValue
        for ItemValue in Document.support_planes
        if ItemValue.id == SketchValue.support_plane_id
    )
    if len(Owners) != 1 or len(Planes) != 1 or Owners[0].sketch_id != SketchValue.id:
        raise ValueError(
            "SOLIDWORKS cold readback lacks an exact feature and datum owner"
        )
    Owner = Owners[0]
    SketchLinks = tuple(
        ItemValue.id
        for ItemValue in Document.feature_timeline
        if ItemValue.id in Owner.input_feature_ids
        and ItemValue.sketch_id == SketchValue.id
    )
    if len(SketchLinks) != 1 or Owner.input_feature_ids != SketchLinks:
        raise ValueError("SOLIDWORKS cold boss requires its owned sketch dependency")
    return Owner, Planes[0]
