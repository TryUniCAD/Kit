# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Any as AnyValue

from convert.api.ApiContext import GetRegistry
from convert.api.Compatibility.ApiCall import MakeApiCall, MakeCallSig


# registry lookup retains its historical private hook for direct module consumers
def MakeRegCall() -> AnyValue:
    return MakeApiCall(
        GetRegistry,
        "_build_registry",
        {},
        {"return": "AdapterRegistry"},
        MakeCallSig((), (), "AdapterRegistry"),
        None,
    )
