from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ParameterRole
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Records.RecordParameter import Parameter


# the sketch radial parameter and both possible boss lengths retain their actual distinct owned order
def ReadCircParams(
    DocumentValue: CadDocument, Definition: ExtrudeFeature
) -> tuple[Parameter, Parameter]:
    SketchValue, FeatureValue = (
        DocumentValue.sketches[0],
        DocumentValue.feature_timeline[0],
    )
    ParamsValue = {Parameter.id: Parameter for Parameter in DocumentValue.parameters}
    LengthsValue = (
        (Definition.length,)
        if Definition.second_length is None
        else (Definition.length, Definition.second_length)
    )
    if (
        len(SketchValue.parameter_ids) != 1
        or len(FeatureValue.parameter_ids) != len(LengthsValue)
        or len(ParamsValue) != 1 + len(LengthsValue)
    ):
        raise ValueError(
            "circle boss requires its owned radial and all active depth drivers"
        )
    RadialParam = ParamsValue[SketchValue.parameter_ids[0]]
    CheckCircDrive(RadialParam, SketchValue.id, "D1")
    BossParams = tuple(ParamsValue[ParamId] for ParamId in FeatureValue.parameter_ids)
    for OrdinalValue, (ParamValue, LengthValue) in enumerate(
        zip(BossParams, LengthsValue, strict=True), 1
    ):
        CheckCircDrive(ParamValue, FeatureValue.id, f"D{OrdinalValue}")
        if ParamValue.value != LengthValue:
            raise ValueError(
                "circle boss depth driver disagrees with its modeled termination"
            )
    return RadialParam, BossParams[0]


# a native reader or writer must not replace an expression or a driven value with literal geometry
def CheckCircDrive(ParamValue: Parameter, OwnerValue: str, NameValue: str) -> None:
    if (
        ParamValue.name != NameValue
        or ParamValue.owner_id != OwnerValue
        or ParamValue.role != ParameterRole.KDriving
        or ParamValue.expression is not None
        or ParamValue.attributes
    ):
        raise ValueError("circle boss requires actual unexpressed driving parameters")
