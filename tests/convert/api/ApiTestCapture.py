# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Any as AnyValue


# capture behavior isolates enforced public options from adapter and filesystem side effects
class CaptureEngine:

    # shared observations let write and conversion calls prove identical option enforcement
    def __init__(
        SelfValue,
        CapturedVals: list[dict[str, object]],
        SentinelValue: object,
    ) -> None:
        SelfValue.CapturedVals = CapturedVals
        SelfValue.SentinelValue = SentinelValue

    # write interception exists because public option enforcement happens before engine delegation
    def WriteTarget(
        SelfValue,
        DocumentData: object,
        TargetData: object,
        *,
        FormatId: str | None,
        WriteOpts: AnyValue,
    ) -> object:
        SelfValue.CapturedVals.append(dict(WriteOpts.values))
        return SelfValue.SentinelValue

    # conversion interception exists because combined calls build their own write options
    def ConvertData(
        SelfValue,
        SourceData: object,
        TargetData: object,
        *,
        SourceFormat: str | None,
        DestFormat: str | None,
        ReadOpts: AnyValue,
        WriteOpts: AnyValue,
    ) -> object:
        SelfValue.CapturedVals.append(dict(WriteOpts.values))
        return SelfValue.SentinelValue
