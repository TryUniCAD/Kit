# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite


# generated builders are bounded data programs rather than arbitrary application or filesystem code
def ProgramSchema():
    return {
        "type": "object",
        "properties": {
            "schema": {"type": "integer", "enum": [1]},
            "operation": {
                "type": "string",
                "enum": ["offset_plane", "coincident_plane"],
            },
            "support": {"type": "string", "enum": ["XY", "YZ", "XZ"]},
            "scale": {"type": "number", "minimum": -2, "maximum": 2},
            "reverse": {"type": "boolean"},
        },
        "required": ["schema", "operation", "support", "scale", "reverse"],
        "additionalProperties": False,
    }


# schema enforcement remains independent of the generating model and its self-reported success
def ValidateProgram(Value):
    if not isinstance(Value, dict) or set(Value) != {
        "schema",
        "operation",
        "support",
        "scale",
        "reverse",
    }:
        raise ValueError("candidate must contain exactly the typed builder fields")
    if type(Value["schema"]) is not int or Value["schema"] != 1:
        raise ValueError("candidate schema must be integer one")
    if Value["operation"] not in ("offset_plane", "coincident_plane") or Value[
        "support"
    ] not in ("XY", "YZ", "XZ"):
        raise ValueError(
            "candidate operation or support is outside the builder language"
        )
    if (
        type(Value["scale"]) not in (int, float)
        or not isfinite(Value["scale"])
        or not -2 <= Value["scale"] <= 2
    ):
        raise ValueError("candidate scale is outside the bounded builder language")
    if type(Value["reverse"]) is not bool:
        raise ValueError("candidate reversal must be a boolean")
    return {**Value, "scale": float(Value["scale"])}
