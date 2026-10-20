# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Any as AnyValue

from convert.adapters.base.ContractTypes import KSourceType, KTargetType
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.engine.Compatibility.EngineCall import MakeCallSig, MakeEngineCall


# deferred loading breaks the facade cycle while conversion result identity is established
def ConvertTarget(
    SelfValue: AnyValue,
    SourceData: KSourceType,
    TargetData: KTargetType,
    *,
    SourceFormat: str | None = None,
    DestFormat: str | None = None,
    ReadOpts: ReadOptions | None = None,
    WriteOpts: WriteOptions | None = None,
) -> AnyValue:
    from convert.engine.EngineConvert import EngineConvert

    return EngineConvert.ConvertData(
        SelfValue,
        SourceData,
        TargetData,
        SourceFormat=SourceFormat,
        DestFormat=DestFormat,
        ReadOpts=ReadOpts,
        WriteOpts=WriteOpts,
    )


# engine conversion retains historical keywords while neutral orchestration remains isolated
def MakeConvertCall() -> AnyValue:
    DefaultsMap = {
        "source_format": None,
        "destination_format": None,
        "read_options": None,
        "write_options": None,
    }
    return MakeEngineCall(
        ConvertTarget,
        "convert",
        {
            "source": "SourceData",
            "destination": "TargetData",
            "source_format": "SourceFormat",
            "destination_format": "DestFormat",
            "read_options": "ReadOpts",
            "write_options": "WriteOpts",
        },
        {
            "source": "Source",
            "destination": "Destination",
            "source_format": "str | None",
            "destination_format": "str | None",
            "read_options": "ReadOptions | None",
            "write_options": "WriteOptions | None",
            "return": "ConversionResult",
        },
        MakeCallSig(
            (("self", None), ("source", "Source"), ("destination", "Destination")),
            (
                ("source_format", "str | None", None),
                ("destination_format", "str | None", None),
                ("read_options", "ReadOptions | None", None),
                ("write_options", "WriteOptions | None", None),
            ),
            "ConversionResult",
        ),
        DefaultsMap,
    )
