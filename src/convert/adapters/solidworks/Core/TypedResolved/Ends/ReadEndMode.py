from collections.abc import Mapping

from interchange.Features.FeatureExtrude import ExtrudeEnd


# actual end specification flags distinguish a blind direction a midpoint total and two independently driving directions
def ReadEndMode(FieldsValue: Mapping[str, object]) -> ExtrudeEnd:
    SingleValue, TypeValue = FieldsValue.get("f08"), FieldsValue.get("f0c")
    ReverseValue = FieldsValue.get("f8c")
    if (
        type(SingleValue) is not int
        or type(TypeValue) is not int
        or type(ReverseValue) is not int
        or ReverseValue not in (0, 1)
        or any(
            type(FieldsValue.get(NameValue)) is not int or FieldsValue[NameValue] != 0
            for NameValue in ("f10", "f88")
        )
    ):
        raise ValueError("extrusion direction and termination flags are unsupported")
    ModesValue = {
        (1, 0): ExtrudeEnd.KBlind,
        (1, 6): ExtrudeEnd.KMidPlane,
        (0, 0): ExtrudeEnd.KTwoLengths,
    }
    ModeValue = ModesValue.get((SingleValue, TypeValue))
    if ModeValue is None:
        raise ValueError("extrusion end mode is outside ordinary boss semantics")
    if (ModeValue != ExtrudeEnd.KBlind or ReverseValue) and (
        FieldsValue.get("f138") is not None
        or FieldsValue.get("f90") is not None
        or any(
            FieldsValue.get(NameValue) != 0
            for NameValue in ("fa0", "fb8", "fbc", "fc0", "fc4")
        )
        or not all(
            IsEndListEmpty(FieldsValue, NameValue) for NameValue in ("f28", "f48")
        )
    ):
        raise ValueError(
            "advanced extrusion direction carries unsupported draft or reference state"
        )
    return ModeValue


# a native save may serialize present zero length arrays without adding any reference semantics
def IsEndListEmpty(FieldsValue: Mapping[str, object], NameValue: str) -> bool:
    Present = FieldsValue.get("has_" + NameValue)
    RowsValue = FieldsValue.get(NameValue)
    if type(Present) is not int:
        return False
    if Present == 0:
        return RowsValue is None
    if Present != 1 or not isinstance(RowsValue, Mapping):
        return False
    CountValue, ItemsValue = RowsValue.get("n"), RowsValue.get("items")
    return (
        type(CountValue) is int
        and CountValue == 0
        and type(ItemsValue) in (list, tuple)
        and not ItemsValue
    )
