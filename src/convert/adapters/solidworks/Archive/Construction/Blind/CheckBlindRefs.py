from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndRefs import (
    BlindEndRefs,
)
from convert.adapters.solidworks.Archive.Construction.Blind.ReadEndParam import (
    ReadEndParam,
)
from convert.adapters.solidworks.Archive.Construction.Blind.RequireEndNode import (
    RequireEndNode,
)


# distinct constructor calls must keep their display parameter and persistent dimension identities independent
def CheckBlindRefs(InputValue: BlindEndInput, RefsValue: BlindEndRefs) -> None:
    FromValue = RequireEndNode(RefsValue.FromEndValue, "moFromEndSpec_c")
    if type(FromValue.FieldsValue["t"]) is not int or FromValue.FieldsValue["t"] != 0:
        raise ValueError("blind construction requires its ordinary from end mode")
    OffsetDisplay = RequireEndNode(
        FromValue.FieldsValue["f28"], "moDisplayDistanceDim_c"
    )
    OrderedValues = (
        RefsValue.ForwardValue,
        RefsValue.ReverseValue,
        RefsValue.ForwardDraft,
        RefsValue.ReverseDraft,
        OffsetDisplay,
    )
    Dimensions = tuple(
        ReadEndParam(InputValue, DisplayValue, OrdinalValue)
        for OrdinalValue, DisplayValue in zip(
            (1, 2, 3, 4, 19), OrderedValues, strict=True
        )
    )
    if len({id(DisplayValue) for DisplayValue in OrderedValues}) != len(OrderedValues):
        raise ValueError("blind constructor displays must have distinct identities")
    if len({Dimension.FieldsValue["f50"] for Dimension in Dimensions}) != len(
        Dimensions
    ):
        raise ValueError(
            "blind constructor dimension identities must be independently allocated"
        )
    if len({id(Dimension.FieldsValue["f28"]) for Dimension in Dimensions}) != len(
        Dimensions
    ):
        raise ValueError("blind constructor parameters must have distinct identities")
