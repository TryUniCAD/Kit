from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import (
    CheckCircDrive,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordParameter import Parameter


# the pocket uses both feature depths and the radial value when its sketch owns one
def ReadPocketDims(
    DocumentValue: CadDocument,
) -> tuple[Parameter, Parameter, Parameter | None]:
    ParamsValue = {
        ParameterValue.id: ParameterValue for ParameterValue in DocumentValue.parameters
    }
    Values: list[Parameter] = []
    for OwnerValue in DocumentValue.feature_timeline:
        if len(OwnerValue.parameter_ids) != 1:
            raise ValueError(
                "ordinary pocket requires one driver for each active owner"
            )
        ParameterValue = ParamsValue[OwnerValue.parameter_ids[0]]
        CheckCircDrive(ParameterValue, OwnerValue.id, "D1")
        Values.append(ParameterValue)
    SketchValue = DocumentValue.sketches[1]
    SketchIds = SketchValue.parameter_ids
    if len(SketchIds) > 1 or len(ParamsValue) != len(Values) + len(SketchIds):
        raise ValueError(
            "ordinary pocket requires every driver to have an actual owner"
        )
    if not SketchIds:
        return Values[0], Values[1], None
    RadialValue = ParamsValue[SketchIds[0]]
    CheckCircDrive(RadialValue, SketchValue.id, "D1")
    return Values[0], Values[1], RadialValue
