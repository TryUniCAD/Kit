# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import ast
from dataclasses import fields, is_dataclass
import json
from pathlib import Path
import sys

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedBase import TypedBase
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.adapters.Fusion.State.EncodeState import EncodeState, KEncodeTypes


def missing_records(model, source_root):
    missing = set()
    pending = [model]
    while pending:
        value = pending.pop()
        cls = type(value)
        if is_dataclass(value):
            if cls not in KEncodeTypes and (cls.__module__, cls.__name__) not in missing:
                module = cls.__module__
                if not module.startswith("convert.Formats.Fusion.BrepCodec.Journal."):
                    return []
                source = source_root.joinpath(*module.split(".")).with_suffix(".py")
                declarations = [node for node in ast.parse(source.read_bytes()).body
                                if isinstance(node, ast.ClassDef) and node.name == cls.__name__]
                if len(declarations) != 1 or cls.__bases__ not in ((object,), (TypedBase,)) or declarations[0].keywords or not all(
                    isinstance(node, ast.AnnAssign) for node in declarations[0].body
                ) or not cls.__dataclass_params__.frozen:
                    return []
                missing.add((module, cls.__name__))
            pending.extend(getattr(value, field.name) for field in fields(value))
        elif isinstance(value, tuple):
            pending.extend(value)
        elif isinstance(value, dict):
            pending.extend(value.values())
    return sorted(missing)


if __name__ == "__main__":
    model = ReadDocument(Path(sys.argv[1]).read_bytes())
    if len(sys.argv) == 3:
        print(json.dumps(missing_records(model, Path(sys.argv[2]))))
    elif DecodeState(EncodeState(model)) != model:
        raise ValueError("decoded semantic state differs from native reader model")
