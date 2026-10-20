# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from inspect import Signature as FuncSig
from typing import Any as AnyValue

from convert.engine.Compatibility.EngineCall import MakeCallSig, MakeEngineCall
from convert.engine.EngineInit import InitEngineMut


# engine construction retains its historical dependency injection signature for custom registries
def MakeConstructor() -> AnyValue:
    return MakeEngineCall(
        InitEngineMut,
        "__init__",
        {"registry": "RegistryData"},
        {"registry": "AdapterRegistry"},
        MakeCallSig(
            (("self", None), ("registry", "AdapterRegistry")),
            (),
            FuncSig.empty,
        ),
        None,
    )
