from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Metadata.ExpandXmlName import (
    ExpandXmlName,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.IsXmlNcName import (
    IsXmlNcName,
)


# element tree serializes qualified attribute values into names bound at the attribute location
def HasXmlAttrs(
    Authored: Mapping[str, str],
    Parsed: Mapping[str, str],
    ScopeValue: Mapping[str, str],
) -> bool:
    if Authored.keys() != Parsed.keys():
        return False
    for NameValue, ValueData in Authored.items():
        SourceValue = CastValue(object, ValueData)
        TextValue = Parsed[NameValue]
        Actual = TextValue
        if not isinstance(SourceValue, str):
            LocalName = TextValue.split(":", 1)[-1]
            if not IsXmlNcName(LocalName):
                return False
            Actual = ExpandXmlName(TextValue, ScopeValue, True)
        if str(SourceValue) != Actual:
            return False
    return True
