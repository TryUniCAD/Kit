# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.ContractCompat import ContractBase


# read policy stays immutable so adapters receive consistent filtering and validation intent
@DataClass(frozen=True, slots=True)
class ReadOptions(ContractBase):
    ConfigName: str | None = None
    IncludeBrep: bool = True
    IncludeMesh: bool = True
    StrictMode: bool = True
    OptionValues: TypeMap[str, AnyValue] = DataField(default_factory=FreezeMapping)
