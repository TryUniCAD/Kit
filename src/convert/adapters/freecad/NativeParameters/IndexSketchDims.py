from collections import Counter
from collections.abc import Mapping

from convert.adapters.freecad.Archive import IsPayloadMap
from convert.adapters.freecad.NativeParameters.ReadEvidence import HasSavedValue
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter
from interchange.geometry.Models.Sketch import Sketch


# pads sharing a sketch need one ambiguity check for its actual dimension owners
def IndexSketchDims(
    SketchValue: Sketch, Parameters: Mapping[str, Parameter]
) -> dict[str, Parameter]:
    DimRows = tuple(
        (Index, RuleValue, Fields, NameValue)
        for Index, RuleValue in enumerate(SketchValue.constraints)
        if IsPayloadMap(Fields := RuleValue.attributes.get("freecad"))
        and isinstance(NameValue := Fields.get("Name"), str)
        and NameValue
    )
    Counts = Counter(NameValue for _, _, _, NameValue in DimRows)
    OwnerIds = set(SketchValue.parameter_ids)
    Result: dict[str, Parameter] = {}
    for Index, RuleValue, Fields, NameValue in DimRows:
        ParamValue = Parameters.get(RuleValue.parameter_id or "")
        if (
            Counts[NameValue] == 1
            and ParamValue is not None
            and not RuleValue.suppressed
            and RuleValue.driving
            and ParamValue.id in OwnerIds
            and ParamValue.owner_id == SketchValue.id
            and ParamValue.expression is None
            and ParamValue.value.kind is ValueKind.KLength
            and ParamValue.attributes.get("freecad_path") == f"Constraints[{Index}]"
            and ParamValue.attributes.get("freecad_constraint") == Fields
            and HasSavedValue(ParamValue)
        ):
            Result[NameValue] = ParamValue
    return Result
