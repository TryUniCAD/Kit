from re import fullmatch as MatchFull
from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)


# a native display dimension carries a typed modifier and fixed decimal precision
def ReadKeyDim(NodeValue: Element) -> KeywordDim:
    if (
        NodeValue.tag != "Dimension"
        or set(NodeValue.attrib) != {"Name"}
        or len(NodeValue)
    ):
        raise ValueError("keyword dimension has an unsupported row structure")
    TextValue = NodeValue.text or ""
    PrefixValue = None
    if TextValue.startswith("<MOD-DIAM>"):
        PrefixValue = "diameter"
        TextValue = TextValue.removeprefix("<MOD-DIAM>")
    elif TextValue.startswith("R"):
        PrefixValue = "radius"
        TextValue = TextValue.removeprefix("R")
    UnitValue = "degree" if TextValue.endswith("°") else None
    TextValue = TextValue.removesuffix("°")
    if MatchFull(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", TextValue) is None:
        raise ValueError(
            "keyword dimension requires the classified decimal display grammar"
        )
    _, Separator, Fraction = TextValue.partition(".")
    NumberValue = float(TextValue) if Separator or TextValue == "-0" else int(TextValue)
    return KeywordDim(
        NodeValue.attrib["Name"], NumberValue, UnitValue, PrefixValue, len(Fraction)
    )
