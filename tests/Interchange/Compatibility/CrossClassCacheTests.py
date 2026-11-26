# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import make_dataclass as MakeRecord
from functools import partial as BindArgs
from types import MappingProxyType as FrozenMap
from typing import cast as CastValue
from typing import Mapping as TypeMap

from interchange.serialization.Deserialize import FromData
from interchange.serialization.MigrationRegistry import KMigrationRegistry, RegMigration
from interchange.serialization.TypeRegistry import KTypeRegistry, RegisterTypes
from tests.Interchange.Fixtures.BindMapHint import BindMapHintMut


# a migration can change another class whose mapping layout was cached earlier in the same decode
def CheckCrossCache() -> None:
    WitnessType = MakeRecord("CacheWitness", [("Metadata", TypeMap[str, object])])
    TriggerType = MakeRecord("CacheTrigger", [("Metadata", dict[str, object])])
    RegisterTypes(WitnessType, TriggerType)
    RegMigration(TriggerType, BindArgs(BindMapHintMut, WitnessType))
    try:
        RestoredValue = FromData(
            [
                {"$type": "CacheWitness", "Metadata": {"mutable": False}},
                {"$type": "CacheTrigger", "Metadata": {"mutable": True}},
                {"$type": "CacheWitness", "Metadata": {"mutable": True}},
            ]
        )
        assert isinstance(RestoredValue, list)
        RecordValues = CastValue(list[object], RestoredValue)
        assert isinstance(getattr(RecordValues[0], "Metadata"), FrozenMap)
        assert isinstance(getattr(RecordValues[2], "Metadata"), dict)
        assert getattr(RecordValues[2], "Metadata") == {"mutable": True}
    finally:
        del KMigrationRegistry[TriggerType]
        del KTypeRegistry["CacheWitness"]
        del KTypeRegistry["CacheTrigger"]
