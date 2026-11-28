from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from interchange.Records.RecordParameter import Parameter
from interchange.Enums.EnumValues import ParameterRole
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature


# a native driving dimension must preserve the actual neutral parameter sketch support configuration and body owners before synthesis
def CheckPlainLinks(
    DocumentValue: CadDocument,
    Definition: ExtrudeFeature,
    *,
    DriverValue: Parameter | None = None,
    AxisValue: str = "z",
) -> None:
    ConfigValue = DocumentValue.configurations[0]
    DepthValue = DocumentValue.parameters[0] if DriverValue is None else DriverValue
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
        DepthValue.role != ParameterRole.KDriving
        or DepthValue.expression is not None
        or DepthValue.owner_id != FeatureValue.id
        or DepthValue.name != "D1"
        or DepthValue.attributes
    ):
        raise ValueError(
            "plain boss requires its actual unexpressed driving D1 parameter"
        )
    if (
        FeatureValue.parameter_ids != (DepthValue.id,)
        or DepthValue.value != Definition.length
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
    if ReadPrincAxis(PlaneValue.transform) != AxisValue:
        raise ValueError("plain boss support has a different canonical principal frame")
