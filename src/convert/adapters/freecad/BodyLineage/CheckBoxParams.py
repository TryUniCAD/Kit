from convert.adapters.freecad.Native import FeatureMut, NativeObject
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# source parameter identity and typed values must agree with their actual primitive owner
def CheckBoxParams(
    Parameters: tuple[Parameter, ...], Child: NativeObject, FeatureValue: FeatureStep
) -> None:
    Expected: list[Parameter] = []
    ExpectedIds = FeatureMut(Child, FeatureValue.id, Expected, set())
    Actual = {Value.id: (Value, type(Value.value.value)) for Value in Parameters}
    if (
        len(Actual) != len(Parameters)
        or len(FeatureValue.parameter_ids) != len(ExpectedIds)
        or set(FeatureValue.parameter_ids) != set(ExpectedIds)
        or Actual != {Value.id: (Value, type(Value.value.value)) for Value in Expected}
    ):
        raise ValueError(
            "FreeCAD origin box parameters disagree with their actual primitive owner"
        )
