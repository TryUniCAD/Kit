# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from interchange import CadDocument

from convert.adapters.base.ContractTypes import KSourceType as Source
from convert.adapters.base.ReadOptions import ReadOptions


# read delegation stays isolated because format discovery belongs entirely to the registry
class EngineRead:

    # registry delegation preserves one validation path for every public document read
    def ReadSource(
        SelfValue,
        SourceData: Source,
        *,
        FormatId: str | None = None,
        ReadOpts: ReadOptions | None = None,
    ) -> CadDocument:
        return getattr(SelfValue, "registry").read(
            SourceData,
            format_id=FormatId,
            options=ReadOpts or ReadOptions(),
        )
