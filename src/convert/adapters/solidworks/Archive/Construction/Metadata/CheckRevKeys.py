from types import MappingProxyType

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)

# exact angular keyword lanes carry the source feature vocabulary and active driver order
KRevKeywordDims = MappingProxyType(
    {
        "Revolve": (
            (("D1", "degree"),),
            (("D1", "degree"), ("D2", "degree")),
            (("D2", "degree"), ("D1", "degree")),
        ),
        "Cut-Revolve": ((("D1", "degree"),),),
        "Revolve-Thin": (
            (("D3", None), ("D1", "degree")),
            (("D1", "degree"), ("D4", None), ("D3", None)),
        ),
    }
)


# angular presentation must identify the observed native feature and all active dimensions
def CheckRevKeys(InputValue: KeywordFeature) -> None:
    KindValue = InputValue.KindValue
    DimsValue = tuple(
        (DimValue.NameValue, DimValue.UnitValue)
        for DimValue in InputValue.DimensionValues
    )
    if (
        KindValue == "Plane"
        and InputValue.TagValue == "Feature"
        and DimsValue == (("D1", "degree"),)
    ):
        return
    if (
        KindValue == "Chamfer"
        and InputValue.TagValue == "Feature"
        and DimsValue == (("D1", None), ("D2", "degree"))
    ):
        return
    if KindValue is None or KindValue not in KRevKeywordDims:
        if any(UnitValue is not None for _, UnitValue in DimsValue):
            raise ValueError(
                "keyword degree suffix requires an ordinary revolve feature"
            )
        return
    if InputValue.TagValue == "Feature" and DimsValue in KRevKeywordDims[KindValue]:
        return
    if KindValue == "Revolve":
        raise ValueError(
            "ordinary revolve keywords require active D1 and optional D2 degree drivers"
        )
    if KindValue == "Cut-Revolve":
        raise ValueError(
            "selected revolve cut keywords require the actual D1 degree driver"
        )
    raise ValueError(
        "thin revolve keywords require their active angle and wall drivers"
    )
