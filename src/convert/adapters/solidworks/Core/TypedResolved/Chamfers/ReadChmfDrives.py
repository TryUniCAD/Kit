from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfDriver import (
    ChmfDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfDim import (
    ReadChmfDim,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# the live archive slots must match the actual mode and stay distinct before neutral parameter binding
def ReadChmfDrives(
    LinkValue: NativeLink, Feature: ArchiveNode, ModeWord: int
) -> tuple[ChmfDriver, ChmfDriver | None, ChmfDriver | None]:
    Fields = Feature.FieldsValue
    Distance = ReadChmfDim(LinkValue, Fields.get("f810"), False)
    AngleValue = ReadChmfDim(LinkValue, Fields["f818"], True) if ModeWord == 1 else None
    SecondValue = (
        ReadChmfDim(LinkValue, Fields["f820"], False, Secondary=True)
        if ModeWord == 2
        else None
    )
    OtherValue = AngleValue or SecondValue
    if (
        OtherValue is not None
        and Distance.DimensionNode.FieldsValue["f50"]
        == OtherValue.DimensionNode.FieldsValue["f50"]
    ):
        raise ValueError(
            "ordinary chamfer drivers reuse a persistent dimension identity"
        )
    if ModeWord != 1 and (
        Distance.ValueSi < 1e-14
        or SecondValue is not None
        and (SecondValue.ValueSi < 1e-14 or SecondValue.ValueSi == Distance.ValueSi)
    ):
        raise ValueError(
            "distance chamfer lacks the modeled independent positive setbacks"
        )
    return Distance, AngleValue, SecondValue
