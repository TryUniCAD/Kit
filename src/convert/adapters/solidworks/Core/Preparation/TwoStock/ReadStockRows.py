from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import Sketch


# profile order follows actual semantic owners independently of neutral collection order
def ReadStockRows(DocumentValue: CadDocument) -> tuple[Sketch, Sketch, Sketch]:
    FrontStock, RightStock, CutValue = DocumentValue.feature_timeline
    Profiles = {SketchValue.id: SketchValue for SketchValue in DocumentValue.sketches}
    ProfileIds = (FrontStock.sketch_id, RightStock.sketch_id, CutValue.sketch_id)
    if (
        not FrontStock.order < RightStock.order < CutValue.order
        or set(ProfileIds) != set(Profiles)
        or any(Value is None for Value in ProfileIds)
    ):
        raise ValueError(
            "two-stock operations must retain their three ordered profile owners"
        )
    FrontDraw, RightDraw, CutDraw = (
        Profiles[Value] for Value in ProfileIds if Value is not None
    )
    if {FrontDraw.support_plane_id, RightDraw.support_plane_id} != {
        PlaneValue.id for PlaneValue in DocumentValue.support_planes
    } or CutDraw.support_plane_id != FrontDraw.support_plane_id:
        raise ValueError(
            "the cut must use the actual Front stock support beside the distinct Right support"
        )
    return FrontDraw, RightDraw, CutDraw
