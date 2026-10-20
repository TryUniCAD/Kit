# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.records.RecordTopology import TopologyCounts


# design bodies connect feature results with topology material and source evidence
@ModelDataMut(
    DefaultMap={
        "Topology": TopologyCounts(),
        "MaterialId": None,
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class DesignBody(ModelBase):
    EntityId: str
    EntityName: str
    FinalFeatureId: str
    Topology: TopologyCounts
    MaterialId: str | None
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
