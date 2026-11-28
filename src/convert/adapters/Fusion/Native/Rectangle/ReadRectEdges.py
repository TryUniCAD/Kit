# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# dependency tuples retain the typed link kind and reject duplicate saved incidences
def ReadRectEdges(Graph: NativeGraph, Value: KEntityValue) -> set[tuple[int, int, int]]:
    Edges = [
        (
            Graph.Resolve(Entry.First).ObjectId,
            Graph.Resolve(Other.First).ObjectId,
            IntegerValue(Other.Second),
        )
        for Entry in MappingItems(Value)
        for Other in MappingItems(Entry.Second)
    ]
    Result = set(Edges)
    if len(Result) != len(Edges):
        raise ValueError("Native rectangle contains duplicated dependency edges")
    return Result
