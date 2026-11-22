from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitFormat import (
    MakeUnitFormat,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KUnitClasses,
    KUnitDomains,
)


# embedded unit fields must follow their concrete constructor and recovered enum domain without class guessing
def MakeUnitFields(
    KindValue: str, UnitCode: int | None, DecimalPlaces: int
) -> dict[str, object]:
    if KindValue not in KUnitClasses:
        raise ValueError("unsupported native unit kind")
    FieldsValue = MakeUnitFormat(DecimalPlaces)
    if KindValue in KUnitDomains:
        if (
            type(CastValue(object, UnitCode)) is not int
            or UnitCode not in KUnitDomains[KindValue]
        ):
            raise ValueError(
                "native unit code is outside its recovered constructor domain"
            )
        FieldsValue["fb0"] = UnitCode
    elif UnitCode is not None:
        raise ValueError("this native unit kind has no independent stored unit code")
    if KindValue == "length":
        FieldsValue["fb8"] = None
    if KindValue == "density":
        FieldsValue.update(
            {"fc0": 3, "fc4": 1, "has_fb8": 0, "fb8": None, "fc8": 3, "fcc": 1}
        )
    return FieldsValue
