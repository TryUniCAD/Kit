# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Any as AnyValue

from convert.api.ApiConvert import ConvertFile
from convert.api.Compatibility.ApiCall import MakeApiCall, MakeCallSig


# conversion retains historical keywords while canonical orchestration stays independently testable
def MakeConvertCall() -> AnyValue:
    DefaultsMap = {
        "source_format": None,
        "destination_format": None,
        "configuration": None,
        "include_brep": True,
        "include_tessellation": True,
        "strict": True,
        "overwrite": False,
        "allow_carrier": True,
        "write_values": None,
    }
    return MakeApiCall(
        ConvertFile,
        "convert",
        {
            "source": "SourceData",
            "destination": "TargetData",
            "source_format": "SourceFormat",
            "destination_format": "DestFormat",
            "configuration": "Configuration",
            "include_brep": "IncludeBrep",
            "include_tessellation": "IncludeTess",
            "strict": "StrictMode",
            "overwrite": "Overwrite",
            "allow_carrier": "AllowCarrier",
            "write_values": "WriteValues",
        },
        {
            "source": "Source",
            "destination": "Destination",
            "source_format": "str | None",
            "destination_format": "str | None",
            "configuration": "str | None",
            "include_brep": "bool",
            "include_tessellation": "bool",
            "strict": "bool",
            "overwrite": "bool",
            "allow_carrier": "bool",
            "write_values": "Mapping[str, Any] | None",
            "return": "ConversionResult",
        },
        MakeCallSig(
            (("source", "Source"), ("destination", "Destination")),
            (
                ("source_format", "str | None", None),
                ("destination_format", "str | None", None),
                ("configuration", "str | None", None),
                ("include_brep", "bool", True),
                ("include_tessellation", "bool", True),
                ("strict", "bool", True),
                ("overwrite", "bool", False),
                ("allow_carrier", "bool", True),
                ("write_values", "Mapping[str, Any] | None", None),
            ),
            "ConversionResult",
        ),
        DefaultsMap,
    )
