# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# mate groups retain source ordering and hierarchy for editable organization
@ModelDataMut(
    DefaultMap={"ParentGroupId": "", "Order": 0, "Provenance": None},
    FactoryMap={"Attributes": FreezeMapping},
)
class MateGroup(ModelBase):
    EntityId: str
    EntityName: str
    OwnerDefinitionId: str
    MateIds: tuple[str, ...]
    ParentGroupId: str
    Order: int
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
