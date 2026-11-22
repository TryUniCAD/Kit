# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import dumps, loads
from pathlib import Path


# source changes must invalidate executable assumptions rather than silently reusing old native bindings
def RecipeHash(RecipeKey):
    Source = Path(__file__).resolve().parents[3] / "FeatureRecipeSpecs.json"
    if Source.is_symlink() or not Source.is_file():
        raise ValueError("written recipe specification must be a regular source file")
    with Source.open("rb") as Stream:
        Raw = Stream.read(4 * 1024 * 1024 + 1)
    if len(Raw) > 4 * 1024 * 1024:
        raise ValueError("written recipe specification exceeds its byte limit")
    Root = loads(Raw)
    if (
        not isinstance(Root, dict)
        or type(Root.get("schema_version")) is not int
        or Root["schema_version"] != 1
    ):
        raise ValueError("unsupported written recipe specification version")
    SourceRows = Root.get("recipes")
    if not isinstance(SourceRows, list) or any(
        not isinstance(Row, dict) for Row in SourceRows
    ):
        raise ValueError("written recipe specification requires a recipe record list")
    Rows = [Row for Row in SourceRows if Row.get("id") == RecipeKey]
    if len(Rows) != 1:
        raise ValueError("executable recipe requires one exact written source row")
    return sha256(
        dumps(
            Rows[0],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
