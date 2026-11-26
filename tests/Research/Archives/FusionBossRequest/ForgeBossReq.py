# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as WriteJson
from json import loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue


# refingerprinting changed request bytes must never overwrite independently prepared evidence
def ForgeBossReq(Request: FilePath, Variant: str) -> bytes:
    Record = CastValue(dict[str, object], ReadJson(Request.read_bytes()))
    Source = CastValue(dict[str, object], Record["source_evidence"])
    if Variant == "owner":
        Source["owner"] = "sldprt:feature:34"
    elif Variant == "span":
        SourceSpans = CastValue(
            list[dict[str, object]], Record["source_relation_provenance"]
        )
        SpanValue = CastValue(list[list[object]], SourceSpans[0]["spans"])[0]
        SpanValue[1] = CastValue(int, SpanValue[1]) + 1
    else:
        RowsValue = CastValue(list[list[object]], Record["source_ordered_relations"])
        if Variant == "origin":
            assert RowsValue[-1][1] == "coincident"
            _ = RowsValue.pop()
        else:
            assert RowsValue[4][1] == "distance"
            Operands = CastValue(list[object], RowsValue[4][2])
            RowsValue[4][2] = Operands[::-1] if Variant == "reverse" else Operands[:1]
    return (
        WriteJson(
            Record,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
