from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane


# each admitted boss requires one active configuration and actual sketch plane and body owners
def CheckPartLinks(DocumentValue: CadDocument) -> SupportPlane:
    ConfigValue = DocumentValue.configurations[0]
    PlaneValue, SketchValue = DocumentValue.support_planes[0], DocumentValue.sketches[0]
    FeatureValue, BodyValue = DocumentValue.feature_timeline[0], DocumentValue.bodies[0]
    if (
        not ConfigValue.active
        or ConfigValue.parent_id is not None
        or ConfigValue.overrides
        or ConfigValue.suppressed_feature_ids
        or ConfigValue.attributes
    ):
        raise ValueError("ordinary boss requires one active independent configuration")
    if (
        FeatureValue.sketch_id != SketchValue.id
        or SketchValue.support_plane_id != PlaneValue.id
    ):
        raise ValueError("ordinary boss requires its actual sketch and support owners")
    if (
        BodyValue.final_feature_id != FeatureValue.id
        or BodyValue.name != FeatureValue.name
        or BodyValue.material_id is not None
        or BodyValue.attributes
    ):
        raise ValueError(
            "ordinary boss body must have its real creating feature and no material"
        )
    if (
        PlaneValue.support_selection_id is not None
        or PlaneValue.offset_parameter_id is not None
        or PlaneValue.attributes
    ):
        raise ValueError("ordinary boss support must be unextended and independent")
    return PlaneValue
