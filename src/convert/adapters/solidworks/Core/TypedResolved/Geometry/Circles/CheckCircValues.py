from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from interchange.Features.FeatureExtrude import ExtrudeEnd


# all four scalar displays retain distinct live dimension and parameter identities while inactive ends cannot hide independent geometry
def CheckCircValues(OwnerValue: ExtrudeOwner) -> None:
    Fields = OwnerValue.EndValue.FieldsValue
    Values = tuple(
        ReadPrismParam(Fields.get(NameValue), Angular)
        for NameValue, Angular in (
            ("f18", False),
            ("f20", False),
            ("fc8", True),
            ("fd0", True),
        )
    )
    if (
        len({Dimension for Dimension, _, _ in Values}) != 4
        or len({Parameter for _, Parameter, _ in Values}) != 4
    ):
        raise ValueError("cache free circle end roles share live owners")
    if len({Dimension.FieldsValue.get("f50") for Dimension, _, _ in Values}) != 4:
        raise ValueError("cache free circle has duplicate end dimension identities")
    if Values[0][2] <= 0 or Values[2][2] != 0 or Values[3][2] != 0:
        raise ValueError("cache free circle has draft or inactive angular controls")
    if Values[0][1] is not OwnerValue.RequireDepth().Parameter:
        raise ValueError("cache free circle depth does not alias its active owner")
    if OwnerValue.ModeValue == ExtrudeEnd.KTwoLengths:
        if (
            OwnerValue.SecondValue is None
            or Values[1][1] is not OwnerValue.SecondValue.Parameter
            or Values[1][2] <= 0
        ):
            raise ValueError("cache free circle second length lacks its active owner")
    elif Values[1][2] != Values[0][2] or OwnerValue.SecondValue is not None:
        raise ValueError("cache free circle has an independent inactive end length")
