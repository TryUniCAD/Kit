from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from convert.adapters.solidworks.Container.Format import (
    SERIALIZED_STRING_MARKER as SerializedStringMarker,
    dimension_scalar_value_offset as DimensionScalarValue,
)
from convert.adapters.solidworks.Core.NativeDimension import NativeDimension

if TYPE_CHECKING:
    from convert.adapters.solidworks.Core.Records.NativeName import NativeName
    from convert.adapters.solidworks.Core.Records.XmlFeature import XmlFeature


# feature instance counts require a named parameter inside a single matching owner interval
def CountFields(
    DataValue: bytes, Features: list[XmlFeature], Names: tuple[NativeName, ...]
) -> list[tuple[int, str, NativeDimension, int, int]]:
    Owners = {Feature.object_id: Feature for Feature in Features}
    if len(Owners) != len(Features):
        return []
    Markers = sorted(
        (ItemValue.offset, ItemValue.object_id)
        for ItemValue in Names
        if ItemValue.object_id in Owners
        and Owners[ItemValue.object_id].name == ItemValue.name
    )
    Occurrences = Counter(Owner for _, Owner in Markers)
    Records: list[tuple[int, str, NativeDimension, int, int]] = []
    for Index, (Start, Owner) in enumerate(Markers):
        Feature = Owners[Owner]
        if Occurrences[Owner] != 1 or Feature.kind.casefold() not in {
            "cirpattern",
            "circularpattern",
            "lpattern",
            "linearpattern",
        }:
            continue
        EndOffset = (
            Markers[Index + 1][0] if Index + 1 < len(Markers) else len(DataValue)
        )
        Dimensions = [
            Dimension
            for Dimension in Feature.dimensions
            if Dimension.name.casefold() == "d1"
        ]
        if len(Dimensions) != 1:
            continue
        NameBytes = Dimensions[0].name.encode("utf-16le")
        NameTag = SerializedStringMarker + bytes([len(NameBytes) // 2]) + NameBytes
        Position = DataValue.find(NameTag, Start, EndOffset)
        if (
            Position < Start + 2
            or DataValue.find(NameTag, Position + len(NameTag), EndOffset) != -1
        ):
            continue
        Token = int.from_bytes(DataValue[Position - 2 : Position], "little")
        Scalar = DimensionScalarValue(DataValue, Position + len(NameTag), EndOffset)
        if 0x8000 <= Token < 0xFFFF and Scalar is not None:
            Records.append(
                (
                    Owner,
                    Feature.kind,
                    Dimensions[0],
                    Scalar,
                    min(EndOffset, Scalar + 512),
                )
            )
    return Records
