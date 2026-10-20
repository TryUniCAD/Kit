# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut


# source spans connect portable entities back to exact native container records
@ModelDataMut(DefaultMap={"RecordKind": ""})
class ProvenanceSpan(ModelBase):
    Stream: str
    Offset: int
    Length: int
    RecordKind: str


# provenance preserves source identity confidence and evidence through conversion pipelines
@ModelDataMut(
    DefaultMap={"NativeId": "", "Confidence": 1.0, "Spans": ()},
    FactoryMap={"Attributes": FreezeMapping},
)
class Provenance(ModelBase):
    Adapter: str
    NativeId: str
    Confidence: float
    Spans: tuple[ProvenanceSpan, ...]
    Attributes: TypeMap[str, AnyValue]
