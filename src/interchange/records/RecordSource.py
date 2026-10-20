# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut


# source identity anchors every portable document to original bytes and application
@ModelDataMut(
    DefaultMap={"ContainerVersion": "", "ApplicationVersion": ""},
    FactoryMap={"Attributes": FreezeMapping},
)
class CadSource(ModelBase):
    FormatId: str
    FilePath: str
    SourceDigest: str
    ContainerVersion: str
    ApplicationVersion: str
    Attributes: TypeMap[str, AnyValue]
