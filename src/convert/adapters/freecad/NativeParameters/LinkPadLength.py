from collections.abc import Mapping
from dataclasses import replace as Replace
from re import compile as CompileRegex

from convert.Geometry.Formula.Arithmetic import EvalFormula, ReadFormula
from convert.Geometry.Formula.FormulaUnits import IsMatchingQty
from convert.adapters.freecad.NativeParameters.FindSketchDim import FindSketchDim
from convert.adapters.freecad.NativeParameters.ReadEvidence import HasSavedValue
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter
from interchange.geometry.Models.Sketch import Sketch

# native object and constraint identifiers stay distinct from display labels
KSketchDivide = CompileRegex(
    r"(?P<sketch>[A-Za-z_][A-Za-z_0-9]{0,127})\.Constraints\."
    + r"(?P<dimension>[A-Za-z_][A-Za-z_0-9]{0,127})[ \t]*/[ \t]*(?P<divisor>[0-9]+)"
)


# editing requires the exact dependency while saved text and dimensions retain their original provenance
def LinkPadLength(
    LengthValue: Parameter,
    SketchValue: Sketch,
    ProfileName: str,
    Source: str,
    Parameters: Mapping[str, Parameter],
) -> Parameter:
    FormulaValue = LengthValue.expression
    if (
        FormulaValue is None
        or FormulaValue.language != "freecad"
        or FormulaValue.parameter_ids
        or FormulaValue.source != Source
        or LengthValue.value.kind is not ValueKind.KLength
        or len(Source) > 1024
    ):
        return LengthValue
    Match = KSketchDivide.fullmatch(Source.strip())
    if Match is None or Match["sketch"] != ProfileName:
        return LengthValue
    Dimension = FindSketchDim(SketchValue, Match["dimension"], Parameters)
    Parsed = ReadFormula(f'sketchLength / {Match["divisor"]}')
    if Dimension is None or Parsed is None or not HasSavedValue(LengthValue):
        return LengthValue
    Evaluated = EvalFormula(Parsed, {"sketchLength": Dimension.value})
    if Evaluated is None or not IsMatchingQty(Evaluated, LengthValue.value):
        return LengthValue
    return Replace(
        LengthValue, expression=Replace(FormulaValue, parameter_ids=(Dimension.id,))
    )
