# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Any as AnyValue

from convert.engine.Compatibility.EngineCall import MakeCallSig, MakeEngineCall
from convert.engine.EngineReader import EngineRead


# engine reads retain historical keywords while registry delegation stays independently testable
def MakeReadCall() -> AnyValue:
    DefaultsMap = {"format_id": None, "options": None}
    return MakeEngineCall(
        EngineRead.ReadSource,
        "read",
        {
            "source": "SourceData",
            "format_id": "FormatId",
            "options": "ReadOpts",
        },
        {
            "source": "Source",
            "format_id": "str | None",
            "options": "ReadOptions | None",
            "return": "CadDocument",
        },
        MakeCallSig(
            (("self", None), ("source", "Source")),
            (
                ("format_id", "str | None", None),
                ("options", "ReadOptions | None", None),
            ),
            "CadDocument",
        ),
        DefaultsMap,
    )
