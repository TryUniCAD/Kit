from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole
from interchange.Features.FeatureKinds import ShellFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# the uniform inward shell must bind the preceding extrusion and its own driving wall thickness
def ReadShellStep(
    ShellValue: FeatureStep, StockValue: FeatureStep, DriverValue: Parameter
) -> tuple[str, float]:
    Definition = ShellValue.definition
    if (
        type(Definition) is not ShellFeature
        or ShellValue.kind != FeatureKind.KShell
        or ShellValue.operation not in (None, BooleanOp.KCutOperation)
        or Definition.outward is not False
        or ShellValue.order <= StockValue.order
        or ShellValue.input_feature_ids != (StockValue.id,)
        or ShellValue.sketch_id is not None
        or ShellValue.suppressed
        or ShellValue.configuration_states
        or ShellValue.attributes
    ):
        raise ValueError("open shell requires one active inward shell on its stock")
    if (
        DriverValue.name != "D1"
        or DriverValue.owner_id != ShellValue.id
        or DriverValue.expression is not None
        or DriverValue.role != ParameterRole.KDriving
        or DriverValue.value != Definition.thickness
        or DriverValue.attributes
    ):
        raise ValueError("open shell thickness requires its actual driving D1")
    return ReadStyleText(ShellValue.name, "shell feature name"), ReadLength(
        Definition.thickness
    )
