from re import fullmatch as FullMatch

from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.Records.RecordParameter import Expression


# native reverse depths need both vendor literal spellings without admitting arbitrary formulas
def ReverseLiteral(NodeValue: NativeNode, Source: str) -> Expression:
    Literal = Source.strip()
    if Literal.startswith("-(") and Literal.endswith(")"):
        Literal = "-" + Literal[2:-1].strip()
    Match = FullMatch(r"-((?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+))\s+mm", Literal)
    if NodeValue.Fields["unit"] != "mm" or Match is None:
        raise ValueError(
            "Native reverse distance requires a negative millimeter literal"
        )
    Amount = float(Match.group(1))
    if Amount <= 0:
        raise ValueError(
            "Native reverse distance requires a negative millimeter literal"
        )
    SameNumbers((-Amount / 10,), (NumberValue(NodeValue.Fields["value"]),))
    return Expression(Source, language="fusion")
