# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumDocument import Severity
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# diagnostics carry recoverable translation issues without invalidating useful documents
@ModelDataMut(
    DefaultMap={
        "Level": Severity.KWarning,
        "EntityId": "",
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class Diagnostic(ModelBase):
    ErrorCode: str
    MessageText: str
    Level: Severity
    EntityId: str
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
