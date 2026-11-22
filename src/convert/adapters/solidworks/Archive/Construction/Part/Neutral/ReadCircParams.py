from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ParameterRole
from interchange.Records.RecordParameter import Parameter


# separate sketch and boss drivers must retain their meaning even though both use the same native name
def ReadCircParams(DocumentValue: CadDocument) -> tuple[Parameter, Parameter]:
    SketchValue, FeatureValue = (
        DocumentValue.sketches[0],
        DocumentValue.feature_timeline[0],
    )
    ParamsValue = {Parameter.id: Parameter for Parameter in DocumentValue.parameters}
    if len(SketchValue.parameter_ids) != 1 or len(FeatureValue.parameter_ids) != 1:
        raise ValueError("circle boss requires its owned radial and depth drivers")
    RadialId, DepthId = SketchValue.parameter_ids[0], FeatureValue.parameter_ids[0]
    if RadialId not in ParamsValue or DepthId not in ParamsValue:
        raise ValueError("circle boss requires its owned radial and depth drivers")
    RadialParam, DepthParam = ParamsValue[RadialId], ParamsValue[DepthId]
    for ValueInput, OwnerValue in (
        (RadialParam, SketchValue.id),
        (DepthParam, FeatureValue.id),
    ):
        CheckCircDrive(ValueInput, OwnerValue, "D1")
    return RadialParam, DepthParam


# independent boss and sketch drivers must remain distinct actual editable parameters
def CheckCircDrive(ParamValue: Parameter, OwnerValue: str, NameValue: str) -> None:
    if (
        ParamValue.name != NameValue
        or ParamValue.owner_id != OwnerValue
        or ParamValue.role != ParameterRole.KDriving
        or ParamValue.expression is not None
        or ParamValue.attributes
    ):
        raise ValueError("circle boss requires two actual unexpressed D1 drivers")
