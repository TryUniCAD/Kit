from __future__ import annotations

from collections.abc import Mapping

from Core import Obj
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


def compatible_model(source):
    memo = {}

    def convert(value):
        if isinstance(value, ArchiveNode):
            key = id(value)
            if key not in memo:
                node = Obj(value.ClassValue.NameValue, schema=value.ClassValue.SchemaValue)
                memo[key] = node
                node.f.update({name: convert(item) for name, item in value.FieldsValue.items()})
            return memo[key]
        if isinstance(value, Mapping):
            return {name: convert(item) for name, item in value.items()}
        if isinstance(value, (tuple, list)):
            return tuple(convert(item) for item in value)
        return value

    return convert(source)
