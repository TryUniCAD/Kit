from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane


# each admitted boss requires one active configuration and actual sketch plane and body owners
def CheckPartLinks(DocumentValue: CadDocument) -> SupportPlane:
    ConfigValue = DocumentValue.configurations[0]
    PlaneValue = DocumentValue.support_planes[0]
    BodyValue = DocumentValue.bodies[0]
    if (
        not ConfigValue.active
        or ConfigValue.parent_id is not None
        or ConfigValue.overrides
        or ConfigValue.suppressed_feature_ids
        or ConfigValue.attributes
    ):
        raise ValueError("ordinary boss requires one active independent configuration")
    for FeatureValue, SketchValue in zip(
        DocumentValue.feature_timeline, DocumentValue.sketches, strict=True
    ):
        if (
            FeatureValue.sketch_id != SketchValue.id
            or SketchValue.support_plane_id != PlaneValue.id
        ):
            raise ValueError(
                "ordinary extrusion requires its actual sketch and support owners"
            )
    if (
        BodyValue.final_feature_id != DocumentValue.feature_timeline[-1].id
        or BodyValue.name != DocumentValue.feature_timeline[0].name
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
