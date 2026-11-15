from __future__ import annotations

import math as MathValue
import re as RegexLib
import struct as Struct

from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.container.Format import VBLISTS_STREAM as KVbStream
from convert.adapters.solidworks.drawing.Models import (
    DrawingSheet,
    DrawingView,
    ViewEdge,
)
from interchange import Vector3

# each view edge record is separated by this native display list stride
KEdgeStride = 204

# the first edge starts this many bytes after its count
KEdgeHeader = 20

# a plausible view holds fewer edges than this guard
KMaxEdges = 5000

KViewName = RegexLib.compile(rb"(?:[ -~]\x00){4,}")


# view names delimit the edge sections inside the vertex buffer stream
def ViewNames(DataValue: bytes) -> tuple[tuple[int, str], ...]:
    Result: list[tuple[int, str]] = []
    for Match in KViewName.finditer(DataValue):
        TextData = Match.group().decode("utf-16le", "replace")
        if "@Drawing View" not in TextData:
            continue
        Result.append((Match.start(), TextData.split("@", 1)[1]))
    return tuple(Result)


# a candidate count is accepted only when every claimed edge record is finite
def Candidates(DataValue: bytes) -> tuple[tuple[int, int, int], ...]:
    Result: list[tuple[int, int, int]] = []
    for CountOffset in range(0, len(DataValue) - KEdgeHeader, 4):
        CountValue = Struct.unpack_from("<I", DataValue, CountOffset)[0]
        if not 2 <= CountValue <= KMaxEdges:
            continue
        Start = CountOffset + KEdgeHeader
        if Start + KEdgeStride * (CountValue - 1) + 48 > len(DataValue):
            continue
        if all(
            (
                all(
                    (
                        MathValue.isfinite(ItemValue) and abs(ItemValue) < 1.0
                        for ItemValue in Struct.unpack_from(
                            "<6d", DataValue, Start + KEdgeStride * Index
                        )
                    )
                )
                for Index in range(CountValue)
            )
        ):
            Result.append((CountOffset, CountValue, Start))
    return tuple(Result)


# edges are bound by drawing view name because vertex buffer order is not sheet order
def ViewEdges(DataValue: bytes) -> dict[str, tuple[ViewEdge, ...]]:
    Names = ViewNames(DataValue)
    Blocks = Candidates(DataValue)
    Result: dict[str, tuple[ViewEdge, ...]] = {}
    Previous = 0
    for NameOffset, ViewName in Names:
        Local = tuple(Block for Block in Blocks if Previous <= Block[0] < NameOffset)
        if not Local:
            Previous = NameOffset
            continue
        _, CountValue, Start = Local[0]
        Edges = tuple(
            ViewEdge(
                Vector3(
                    *Struct.unpack_from("<3d", DataValue, Start + KEdgeStride * Index)
                ),
                Vector3(
                    *Struct.unpack_from(
                        "<3d", DataValue, Start + KEdgeStride * Index + 24
                    )
                ),
            )
            for Index in range(CountValue)
        )
        if ViewName in Result:
            raise SldprtFormatError("drawing edge list repeats a view")
        Result[ViewName] = Edges
        Previous = NameOffset
    return Result


# edge recovery needs the vertex buffer stream and a complete view match
def EdgeSheets(
    Sheets: tuple[DrawingSheet, ...], Archive: SldprtArchive
) -> tuple[DrawingSheet, ...]:
    DataValue = Archive.get(KVbStream)
    if DataValue is None:
        raise SldprtFormatError(f"drawing is missing {KVbStream}")
    return AttachEdges(Sheets, ViewEdges(DataValue))


# every parsed view must have a matching edge block before geometry is returned
def AttachEdges(
    Sheets: tuple[DrawingSheet, ...], EdgeMap: dict[str, tuple[ViewEdge, ...]]
) -> tuple[DrawingSheet, ...]:
    from dataclasses import replace as ReplaceData

    if not EdgeMap:
        raise SldprtFormatError("drawing has no recoverable view edges")
    NewSheets: list[DrawingSheet] = []
    SeenNames: set[str] = set()
    for SheetValue in Sheets:
        NewViews: list[DrawingView] = []
        for ViewValue in SheetValue.Views:
            Edges = EdgeMap.get(ViewValue.Name)
            if Edges is None:
                raise SldprtFormatError("drawing view has no edge block")
            NewViews.append(ReplaceData(ViewValue, Edges=Edges))
            SeenNames.add(ViewValue.Name)
        NewSheets.append(ReplaceData(SheetValue, Views=tuple(NewViews)))
    if SeenNames != set(EdgeMap):
        raise SldprtFormatError("drawing edge block names an unknown view")
    return tuple(NewSheets)
