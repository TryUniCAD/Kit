from __future__ import annotations

from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Ends.ReadEndMode import (
    IsEndListEmpty,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


@dataclass(frozen=True, slots=True)
class ThroughAllEnd:
    EndValue: ArchiveNode
    ModeValue: str = "through_all"
    IsReversed: bool = True
    IsSingleEnded: bool = True
    ForwardDepth: None = None
    ReverseDepth: None = None


def read_through_end(node):
    node = RequireNative(node, "moICE_c")
    if node.ClassValue.SchemaValue != 1 or node.FieldsValue.get("f810") != 1:
        raise ValueError(
            "the disclosed through-all grammar requires an ordinary schema-one solid cut"
        )
    end = RequireNative(node.FieldsValue.get("f818"), "moEndSpec_c")
    values = end.FieldsValue
    if end.ClassValue.SchemaValue != 1 or tuple(
        values.get(key) for key in ("f08", "f0c", "f10", "f88", "f8c")
    ) != (1, 1, 0, 0, 1):
        raise ValueError("the disclosed grammar requires one forward type-one cut end")
    if any(
        values.get(key) is not None
        for key in ("f18", "f20", "fc8", "fd0", "f138", "f90")
    ):
        raise ValueError(
            "the through-all end cannot supply an active distance, draft or custom direction owner"
        )
    if any(
        values.get(key) != 0
        for key in (
            "fa0",
            "fb8",
            "fbc",
            "fc0",
            "fc4",
            "fb0",
            "fb4",
            "fa8",
            "fac",
            "fd8",
            "fdc",
            "f12c",
            "f130",
            "f148",
            "f14c",
        )
    ):
        raise ValueError(
            "the disclosed end has unsupported draft or alternate termination state"
        )
    if not all(IsEndListEmpty(values, key) for key in ("f28", "f48")):
        raise ValueError(
            "the disclosed through-all end has an external target collection"
        )
    start = RequireNative(values.get("f140"), "moFromEndSpec_c")
    if start.ClassValue.SchemaValue != 1 or start.FieldsValue != {"t": 0}:
        raise ValueError(
            "the disclosed through-all cut must start on its actual profile"
        )
    return ThroughAllEnd(end)
