# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from interchange import CadDocument

from convert.adapters.base.ContractTypes import KTargetType as Destination
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult


# write delegation stays isolated because output staging belongs entirely to the registry
class EngineWrite:

    # registry delegation preserves one validation path for every public document write
    def WriteTarget(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: Destination,
        *,
        FormatId: str | None = None,
        WriteOpts: WriteOptions | None = None,
    ) -> WriteResult:
        return getattr(SelfValue, "registry").write(
            DocumentData,
            TargetData,
            format_id=FormatId,
            options=WriteOpts or WriteOptions(),
        )
