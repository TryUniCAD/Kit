# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# component definitions describe reusable nodes independently from their occurrences
@ModelDataMut(
    DefaultMap={
        "DocumentId": "",
        "ConfigurationName": "",
        "ConfigurationId": "",
        "BoundingBox": None,
        "BodyIds": (),
        "MeshIds": (),
        "SourcePath": "",
        "SourceFormatId": "",
        "SourceDigest": "",
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class ComponentDef(ModelBase):
    EntityId: str
    EntityName: str
    EntityKind: ComponentKind | str
    DocumentId: str
    ConfigurationName: str
    ConfigurationId: str
    BoundingBox: BoundingBox | None
    BodyIds: tuple[str, ...]
    MeshIds: tuple[str, ...]
    SourcePath: str
    SourceFormatId: str
    SourceDigest: str
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
