from __future__ import annotations

import struct
from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


def resolved_signature(state, extra=None):
    pins = {id(entry.EntryValue): entry.IndexValue for entry in state.state.EntriesValue if isinstance(entry.EntryValue, ArchiveNode)}
    embedded, active = {}, set()

    def value(item):
        if isinstance(item, ArchiveNode):
            if id(item) in pins:
                return ("reference", pins[id(item)])
            if id(item) in active:
                return ("embedded_reference", embedded[id(item)])
            label = embedded.setdefault(id(item), len(embedded))
            active.add(id(item))
            return ("embedded", label, item.ClassValue, value(item.FieldsValue))
        if isinstance(item, Mapping):
            return {key: value(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return (type(item).__name__, [value(child) for child in item])
        if isinstance(item, float):
            return ("float64", struct.pack("<d", item).hex())
        return item

    rows = []
    for entry in state.state.EntriesValue:
        node = entry.EntryValue
        if isinstance(node, ArchiveNode):
            rows.append((entry.IndexValue, node.ClassValue, value(node.FieldsValue), (node.StartOffset, node.EndOffset, node.IndexValue)))
        else:
            rows.append((entry.IndexValue, node))
    return state.count, rows, value(extra)
