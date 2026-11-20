from collections.abc import Mapping
from re import fullmatch as MatchName
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.CheckPropText import (
    CheckPropText,
)


# ordinary literal property rows need distinct names and values that do not require an expression evaluator
def ReadPropRows(
    ValuesValue: Mapping[str, object],
) -> tuple[tuple[str, str], ...]:
    if (
        not isinstance(CastValue(object, ValuesValue), Mapping)
        or len(ValuesValue) > 4096
    ):
        raise ValueError("part properties require a bounded text mapping")
    SeenNames: set[str] = set()
    PropertyRows: list[tuple[str, str]] = []
    for NameValue, RawText in ValuesValue.items():
        if not isinstance(CastValue(object, NameValue), str) or not MatchName(
            r"[A-Za-z][A-Za-z0-9 _.-]{0,127}", NameValue
        ):
            raise ValueError(
                "custom property name lies outside the ordinary text profile"
            )
        NormalName = NameValue.casefold()
        if NormalName in SeenNames:
            raise ValueError("custom property names must be distinct within a scope")
        TextValue = CheckPropText(RawText)
        if TextValue.lstrip().casefold().startswith(("=", "$prp")):
            raise ValueError("ordinary text properties require literal unlinked values")
        SeenNames.add(NormalName)
        PropertyRows.append((NameValue, TextValue))
    return tuple(PropertyRows)
