# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Any as AnyValue

from convert.api.ApiBrep import ExtractBrep
from convert.api.Compatibility.ApiCall import MakeApiCall, MakeCallSig


# brep extraction retains historical paths and keywords while canonical payload logic stays isolated
def MakeBrepCall() -> AnyValue:
    DefaultsMap = {"source_format": None, "overwrite": False}
    return MakeApiCall(
        ExtractBrep,
        "extract_brep",
        {
            "source": "SourceData",
            "directory": "FolderPath",
            "source_format": "SourceFormat",
            "overwrite": "Overwrite",
        },
        {
            "source": "Source | CadDocument",
            "directory": "str | Path",
            "source_format": "str | None",
            "overwrite": "bool",
            "return": "tuple[Path, ...]",
        },
        MakeCallSig(
            (("source", "Source | CadDocument"), ("directory", "str | Path")),
            (
                ("source_format", "str | None", None),
                ("overwrite", "bool", False),
            ),
            "tuple[Path, ...]",
        ),
        DefaultsMap,
    )
