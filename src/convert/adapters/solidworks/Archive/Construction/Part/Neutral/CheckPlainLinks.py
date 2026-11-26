from interchange.Enums.EnumValues import ParameterRole
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature


# a native driving dimension must preserve the actual neutral parameter sketch support configuration and body owners before synthesis
def CheckPlainLinks(DocumentValue: CadDocument, Definition: ExtrudeFeature) -> None:
    ConfigValue, Parameter = (
        DocumentValue.configurations[0],
        DocumentValue.parameters[0],
    )
    PlaneValue, SketchValue = DocumentValue.support_planes[0], DocumentValue.sketches[0]
    FeatureValue, BodyValue = DocumentValue.feature_timeline[0], DocumentValue.bodies[0]
    if (
        not ConfigValue.active
        or ConfigValue.parent_id is not None
        or ConfigValue.overrides
        or ConfigValue.suppressed_feature_ids
        or ConfigValue.attributes
    ):
        raise ValueError(
            "plain boss requires one active unmodified independent configuration"
        )
    if (
        FeatureValue.sketch_id != SketchValue.id
        or SketchValue.support_plane_id != PlaneValue.id
    ):
        raise ValueError(
            "plain boss sketch and support ownership differ from the actual neutral references"
        )
    if (
        Parameter.role != ParameterRole.KDriving
        or Parameter.expression is not None
        or Parameter.owner_id != FeatureValue.id
        or Parameter.name != "D1"
        or Parameter.attributes
    ):
        raise ValueError(
            "plain boss requires its actual unexpressed driving D1 parameter"
        )
    if (
        FeatureValue.parameter_ids != (Parameter.id,)
        or Parameter.value != Definition.length
    ):
        raise ValueError(
            "plain boss feature definition and driving parameter values disagree"
        )
    if (
        BodyValue.final_feature_id != FeatureValue.id
        or BodyValue.name != FeatureValue.name
        or BodyValue.material_id is not None
        or BodyValue.attributes
    ):
        raise ValueError(
            "plain boss body must belong to its actual creating feature without extra material state"
        )
    if (
        PlaneValue.support_selection_id is not None
        or PlaneValue.offset_parameter_id is not None
        or PlaneValue.attributes
    ):
        raise ValueError(
            "plain boss does not admit attached offset or extended support semantics"
        )
    TransformValue = PlaneValue.transform
    if (
        TransformValue.origin.x,
        TransformValue.origin.y,
        TransformValue.origin.z,
        TransformValue.x_axis.x,
        TransformValue.x_axis.y,
        TransformValue.x_axis.z,
        TransformValue.y_axis.x,
        TransformValue.y_axis.y,
        TransformValue.y_axis.z,
        TransformValue.z_axis.x,
        TransformValue.z_axis.y,
        TransformValue.z_axis.z,
    ) != (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        raise ValueError(
            "plain boss support must be the canonical front plane at the model origin"
        )
