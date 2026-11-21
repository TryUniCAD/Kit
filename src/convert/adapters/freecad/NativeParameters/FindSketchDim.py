from collections.abc import Mapping

from convert.adapters.freecad.Archive import IsPayloadMap
from convert.adapters.freecad.NativeParameters.ReadEvidence import HasSavedValue
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter
from interchange.geometry.Models.Sketch import Sketch


# names identify constraints only inside the actual sketch and its typed parameter inventory
def FindSketchDim(
    SketchValue: Sketch, NameValue: str, Parameters: Mapping[str, Parameter]
) -> Parameter | None:
    Matches = tuple(
        (Index, RuleValue, Fields)
        for Index, RuleValue in enumerate(SketchValue.constraints)
        if IsPayloadMap(Fields := RuleValue.attributes.get("freecad"))
        and Fields.get("Name") == NameValue
    )
    if len(Matches) != 1:
        return None
    Index, RuleValue, Fields = Matches[0]
    ParamValue = Parameters.get(RuleValue.parameter_id or "")
    if (
        ParamValue is None
        or RuleValue.suppressed
        or not RuleValue.driving
        or ParamValue.id not in SketchValue.parameter_ids
        or ParamValue.owner_id != SketchValue.id
        or ParamValue.expression is not None
        or ParamValue.value.kind is not ValueKind.KLength
        or ParamValue.attributes.get("freecad_path") != f"Constraints[{Index}]"
        or ParamValue.attributes.get("freecad_constraint") != Fields
        or not HasSavedValue(ParamValue)
    ):
        return None
    return ParamValue
