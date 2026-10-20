# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.engine.Compatibility.ConstructorCall import MakeConstructor
from convert.engine.Compatibility.ConvertCall import MakeConvertCall
from convert.engine.Compatibility.EngineCall import SetResultType
from convert.engine.Compatibility.ReadCall import MakeReadCall
from convert.engine.Compatibility.WriteCall import MakeWriteCall


# dynamic composition preserves the historical class surface without merging engine responsibilities
def BuildEngine(ResultType: type) -> type:
    SetResultType(ResultType)
    ClassScope = {
        "__init__": MakeConstructor(),
        "read": MakeReadCall(),
        "write": MakeWriteCall(),
        "convert": MakeConvertCall(),
    }
    EngineType = type("ConversionEngine", (), ClassScope)
    EngineType.__module__ = "convert.engine"
    return EngineType
