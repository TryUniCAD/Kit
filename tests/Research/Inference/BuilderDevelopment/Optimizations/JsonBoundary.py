# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from typing import cast as TypeCast


# decoded records must prove their shape before fixtures inspect nested protocol evidence
def AsRecord(Value: object) -> dict[str, object]:
    assert isinstance(Value, dict)
    return TypeCast(dict[str, object], Value)


# receipt lists retain checked record shapes instead of leaking untyped json into assertions
def AsRecords(Value: object) -> list[dict[str, object]]:
    assert isinstance(Value, list)
    return [AsRecord(Entry) for Entry in TypeCast(list[object], Value)]


# persisted evidence enters fixtures through a checked json object boundary
def ReadRecord(Value: str | bytes) -> dict[str, object]:
    return AsRecord(DecodeJson(Value))


# child configuration contains paths and modes whose string contract is checked before dispatch
def ReadConfig(Value: str | bytes) -> dict[str, str]:
    Record = ReadRecord(Value)
    assert all(isinstance(Entry, str) for Entry in Record.values())
    return TypeCast(dict[str, str], Record)


# protocol string fields cannot become arbitrary objects through a malformed fixture record
def TextField(Record: dict[str, object], FieldName: str) -> str:
    Value = Record[FieldName]
    assert isinstance(Value, str)
    return Value


# socket ports preserve their integer contract without accepting booleans as integer subclasses
def CountField(Record: dict[str, object], FieldName: str) -> int:
    Value = Record[FieldName]
    assert type(Value) is int
    return Value
