from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from convert.formats.Fusion.EntityCodec.Schema.WireType import KWireKind

if TYPE_CHECKING:
    from tests.convert.formats.FusionCodec.Entities.FieldJson import FieldJson


class WireJson(TypedDict):
    KindValue: KWireKind
    Arguments: list[WireJson]
    Members: list[FieldJson]
    ClassGuid: str
    FixedCount: int
    AllowedInts: list[int]
    HasMatrixRows: bool
