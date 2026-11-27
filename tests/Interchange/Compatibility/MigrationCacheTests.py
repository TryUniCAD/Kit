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
from typing import Mapping as TypeMap
from typing import cast as CastValue

from interchange.serialization.Deserialize import FromData
from interchange.serialization.MigrationRegistry import KMigrationRegistry, RegMigration
from interchange.serialization.TypeRegistry import KTypeRegistry, RegisterTypes
from tests.Interchange.Fixtures.BindMapHint import BindMapHintMut


# migrations must refresh mapping ownership for later records inside one public decoding operation
def CheckMigrateMap() -> None:
    RecordType = MakeRecord("CacheMigrated", [("Metadata", TypeMap[str, object])])
    RegisterTypes(RecordType)
    RegMigration(RecordType, BindArgs(BindMapHintMut, RecordType))
    try:
        RestoredValue = FromData(
            [
                {"$type": "CacheMigrated", "Metadata": {"mutable": False}},
                {"$type": "CacheMigrated", "Metadata": {"mutable": True}},
            ]
        )
        assert isinstance(RestoredValue, list)
        RecordValues = CastValue(list[object], RestoredValue)
        assert isinstance(getattr(RecordValues[0], "Metadata"), FrozenMap)
        assert isinstance(getattr(RecordValues[1], "Metadata"), dict)
        assert getattr(RecordValues[1], "Metadata") == {"mutable": True}
    finally:
        del KMigrationRegistry[RecordType]
        del KTypeRegistry["CacheMigrated"]
