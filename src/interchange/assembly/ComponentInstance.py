# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.assembly.TransformMatrix import TransformMatrix


# component instances preserve placement order suppression and configuration choices
@ModelDataMut(
    DefaultMap={
        "Transform": TransformMatrix(),
        "Order": 0,
        "ReferenceNumber": "",
        "ConfigurationName": "",
        "ConfigurationId": "",
        "IsSuppressed": False,
        "IsHidden": False,
        "IsFixed": False,
        "IsFlexible": False,
        "IsExcludedBom": False,
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class ComponentInst(ModelBase):
    EntityId: str
    EntityName: str
    DefinitionId: str
    OwnerDefinitionId: str
    Transform: TransformMatrix
    Order: int
    ReferenceNumber: str
    ConfigurationName: str
    ConfigurationId: str
    IsSuppressed: bool
    IsHidden: bool
    IsFixed: bool
    IsFlexible: bool
    IsExcludedBom: bool
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
