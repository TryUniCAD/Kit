# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import make_dataclass as MakeRecord
from types import MappingProxyType as FrozenMap
from typing import Mapping as TypeMap

from interchange.serialization.Deserialize import FromData
from interchange.serialization.TypeRegistry import KTypeRegistry, RegisterTypes


# inherited extension annotations may change between public decodes without leaving stale mapping ownership
def CheckHintChange() -> None:
    ParentType = MakeRecord("CacheParent", [("Metadata", TypeMap[str, object])])
    RecordType = MakeRecord("CacheChild", [], bases=(ParentType,))
    RegisterTypes(RecordType)
    SourceValue = {"$type": "CacheChild", "Metadata": {"value": 7}}
    try:
        FrozenValue = FromData(SourceValue)
        assert isinstance(getattr(FrozenValue, "Metadata"), FrozenMap)
        setattr(ParentType, "__annotations__", {"Metadata": dict[str, object]})
        MutableValue = FromData(SourceValue)
        assert isinstance(getattr(MutableValue, "Metadata"), dict)
        ParentType.__annotations__["Metadata"] = TypeMap[str, object]
        FreshValue = FromData(SourceValue)
        assert isinstance(getattr(FreshValue, "Metadata"), FrozenMap)
        assert getattr(FreshValue, "Metadata") == {"value": 7}
    finally:
        del KTypeRegistry["CacheChild"]
