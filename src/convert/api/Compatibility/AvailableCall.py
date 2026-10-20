# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Any as AnyValue

from convert.api.ApiAvailable import ListAdapters
from convert.api.Compatibility.ApiCall import MakeApiCall, MakeCallSig


# adapter discovery keeps its historical callable identity for schema and pickle consumers
def MakeAvailable() -> AnyValue:
    return MakeApiCall(
        ListAdapters,
        "available_adapters",
        {},
        {"return": "tuple[AdapterInfo, ...]"},
        MakeCallSig((), (), "tuple[AdapterInfo, ...]"),
        None,
    )
