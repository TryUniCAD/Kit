from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import (
    DistanceInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.MateConstraint import MateConstraint
from interchange.Records.RecordParameter import Parameter


# a positive distance must retain its real owned driving parameter rather than an unrelated cached numeric value
def ReadAsmLength(
    Value: MateConstraint, Parameters: Mapping[str, Parameter]
) -> DistanceInput | None:
    if str(Value.kind) != "distance":
        RequireAsm(
            Value.value is None and not Value.parameter_ids,
            "nondimensional mate contains an unrepresented value",
        )
        return None
    RequireAsm(
        Value.value is not None and len(Value.parameter_ids) == 1,
        "positive distance requires one actual owned driving parameter",
    )
    if Value.value is None:
        raise ValueError("positive distance requires its actual value")
    ParameterValue = Parameters[Value.parameter_ids[0]]
    RequireAsm(
        ParameterValue.name == "D1"
        and str(ParameterValue.role) == "driving"
        and ParameterValue.owner_id == Value.id,
        "distance parameter identity or ownership differs",
    )
    RequireAsm(
        ParameterValue.expression is None
        and ParameterValue.provenance is None
        and not ParameterValue.attributes,
        "distance parameter has unprojected expression or extension state",
    )
    RequireAsm(
        ParameterValue.value == Value.value, "mate and parameter live lengths differ"
    )
    return DistanceInput(ReadLength(Value.value), False, 0)
