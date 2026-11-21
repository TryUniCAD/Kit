from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureExtrude import ExtrudeEnd


# blind scalar mode flags do not prove the absence of retained draft reference or start offset controls
def CheckPrismEnd(
    OwnerValue: ExtrudeOwner,
    *,
    ReversedBlind: bool = False,
    SelectedMidPlane: bool = False,
) -> None:
    Fields = OwnerValue.EndValue.FieldsValue
    EndCode = 6 if OwnerValue.ModeValue == ExtrudeEnd.KMidPlane else 0
    if (
        any(
            Fields.get(FieldName) != (EndCode if FieldName == "f0c" else 0)
            for FieldName in KBlindZeroFields
        )
        or Fields.get("f08") != 1
        or Fields.get("f8c") != int(ReversedBlind)
        or Fields.get("f128") != 1
    ):
        raise ValueError("cache free prism has unsupported termination options")
    if (
        Fields.get("f138") is not None
        or Fields.get("f90") is not None
        or Fields.get("fa0") != 0.0
    ):
        raise ValueError("cache free prism has reference or draft termination state")
    if not IsLineState(Fields.get("fe0")) or not IsLineState(Fields.get("f100")):
        raise ValueError("cache free prism has end selection collections")
    FromValue = RequireNative(Fields.get("f140"), "moFromEndSpec_c")
    if FromValue.FieldsValue != {"t": 0}:
        raise ValueError("cache free prism has a nonordinary start owner")
    NullReverse = (
        SelectedMidPlane
        and OwnerValue.ModeValue == ExtrudeEnd.KMidPlane
        and not OwnerValue.IsReversed
        and not ReversedBlind
        and OwnerValue.SecondValue is None
        and OwnerValue.SecondModeValue is None
        and "f20" in Fields
        and Fields["f20"] is None
    )
    Values = tuple(
        ReadPrismParam(Fields.get(FieldName), Angular)
        for FieldName, Angular in (
            ("f18", False),
            ("f20", False),
            ("fc8", True),
            ("fd0", True),
        )
        if not (NullReverse and FieldName == "f20")
    )
    if len({Dimension for Dimension, _, _ in Values}) != len(Values) or len(
        {Parameter for _, Parameter, _ in Values}
    ) != len(Values):
        raise ValueError("cache free prism end roles share live owners")
    if (
        Values[0][2] <= 0
        or (not NullReverse and Values[1][2] != Values[0][2])
        or Values[-2][2] != 0
        or Values[-1][2] != 0
    ):
        raise ValueError(
            "cache free prism has draft or independent inactive end controls"
        )
    DimensionIds = tuple(Dimension.FieldsValue.get("f50") for Dimension, _, _ in Values)
    if len(set(DimensionIds)) != len(Values):
        raise ValueError("cache free prism has duplicated end dimension identities")
    if NullReverse and any(
        type(Identity) is not int or Identity < 0 for Identity in DimensionIds
    ):
        raise ValueError("cache free stock end dimension lacks its persistent identity")
    DepthValue = OwnerValue.RequireDepth()
    if Values[0][1] is not DepthValue.Parameter or (
        NullReverse
        and (
            Fields["f18"] is not DepthValue.DisplayValue
            or Values[0][0] is not DepthValue.Dimension
            or DepthValue.DepthValue.name != "D1"
        )
    ):
        raise ValueError(
            "cache free prism active depth does not alias its selected live owner"
        )
