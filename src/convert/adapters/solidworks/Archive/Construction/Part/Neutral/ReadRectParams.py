from interchange.Enums.EnumValues import ParameterRole
from interchange.Records.RecordParameter import Parameter
from interchange.document.Models.DocumentModel import CadDocument


# the three real driving lengths must preserve their sketch and boss ownership without relying on input parameter order
def ReadRectParams(
    DocumentValue: CadDocument,
) -> tuple[Parameter, Parameter, Parameter]:
    SketchValue, FeatureValue = (
        DocumentValue.sketches[0],
        DocumentValue.feature_timeline[0],
    )
    OwnersValue = (
        (SketchValue.id, "D1"),
        (SketchValue.id, "D2"),
        (FeatureValue.id, "D1"),
    )
    Parameters: list[Parameter] = []
    for OwnerId, NameValue in OwnersValue:
        Matches = tuple(
            ParamValue
            for ParamValue in DocumentValue.parameters
            if (ParamValue.owner_id, ParamValue.name) == (OwnerId, NameValue)
        )
        if len(Matches) != 1:
            raise ValueError(
                "dimensioned rectangle requires unique owned sketch D1 D2 and boss D1 parameters"
            )
        ParamValue = Matches[0]
        if (
            ParamValue.role != ParameterRole.KDriving
            or ParamValue.expression is not None
            or ParamValue.attributes
        ):
            raise ValueError(
                "rectangle lengths require unexpressed unextended driving parameters"
            )
        Parameters.append(ParamValue)
    WidthParam, HeightParam, DepthParam = Parameters
    if SketchValue.parameter_ids != (
        WidthParam.id,
        HeightParam.id,
    ) or FeatureValue.parameter_ids != (DepthParam.id,):
        raise ValueError(
            "rectangle parameter collections must preserve the actual ordered owners"
        )
    return WidthParam, HeightParam, DepthParam
