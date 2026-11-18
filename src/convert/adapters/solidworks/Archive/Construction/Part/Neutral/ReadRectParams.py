from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadDriverName import (
    ReadDriverName,
)
from interchange.Enums.EnumValues import ParameterRole
from interchange.Records.RecordParameter import Parameter
from interchange.document.Models.DocumentModel import CadDocument


# actual ordered owner identifiers determine rectangle driver roles independently of their authored names
def ReadRectParams(
    DocumentValue: CadDocument,
) -> tuple[Parameter, Parameter, Parameter]:
    SketchValue, FeatureValue = (
        DocumentValue.sketches[0],
        DocumentValue.feature_timeline[0],
    )
    if len(SketchValue.parameter_ids) != 2 or len(FeatureValue.parameter_ids) != 1:
        raise ValueError("rectangle requires two sketch drivers and one boss driver")
    IdValues = (*SketchValue.parameter_ids, *FeatureValue.parameter_ids)
    if len(set(IdValues)) != len(IdValues):
        raise ValueError("rectangle parameter roles must have unique identities")
    OwnersValue = (SketchValue.id, SketchValue.id, FeatureValue.id)
    Indexed = {ParamValue.id: ParamValue for ParamValue in DocumentValue.parameters}
    Parameters: list[Parameter] = []
    for IdentityValue, OwnerId in zip(IdValues, OwnersValue, strict=True):
        ParamValue = Indexed.get(IdentityValue)
        if ParamValue is None or ParamValue.owner_id != OwnerId:
            raise ValueError("rectangle parameter is missing its actual feature owner")
        if (
            ParamValue.role != ParameterRole.KDriving
            or ParamValue.expression is not None
            or ParamValue.attributes
        ):
            raise ValueError(
                "rectangle lengths require unexpressed unextended driving parameters"
            )
        _ = ReadDriverName(ParamValue.name)
        Parameters.append(ParamValue)
    WidthParam, HeightParam, DepthParam = Parameters
    if WidthParam.name.casefold() == HeightParam.name.casefold():
        raise ValueError(
            "rectangle sketch requires two distinct driving parameter names"
        )
    return WidthParam, HeightParam, DepthParam
