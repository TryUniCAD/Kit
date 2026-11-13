from functools import cache as CacheValue
from importlib.resources import files as ReadResources
from json import loads as LoadJson
from lzma import decompress as Decompress
from types import MappingProxyType as ReadOnlyMap
from typing import Mapping as KMapping
from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilCurve import (
    StencilCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilFace import (
    StencilFace,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilJson import (
    KKnotJson,
    StencilsJson,
    TableJson,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilTable import (
    StencilTable,
)


def ReadKnots(Entries: KKnotJson) -> tuple[SplineKnot, ...]:
    return tuple(SplineKnot(float(Value), int(Count)) for Value, Count in Entries)


def ReadTable(Entry: TableJson) -> StencilTable:
    RowValues = tuple(
        tuple((int(GripIndex), float(Value)) for GripIndex, Value in RowValue)
        for RowValue in Entry["Rows"]
    )
    Faces = tuple(
        StencilFace(int(FaceIndex), ReadKnots(KnotsU), ReadKnots(KnotsV), tuple(Poles))
        for FaceIndex, KnotsU, KnotsV, Poles in Entry["Faces"]
    )
    Curves = tuple(
        StencilCurve(
            tuple(float(Value) for Value in Knots), tuple(Counts), tuple(Poles)
        )
        for Knots, Counts, Poles in Entry["Curves"]
    )
    Table = StencilTable(
        str(Entry["Label"]),
        str(Entry["LayoutKey"]),
        int(Entry["GripCount"]),
        RowValues,
        Faces,
        Curves,
        tuple(Entry["Points"]),
    )
    UsedRows = {Index for FaceValue in Faces for Index in FaceValue.Poles}
    UsedRows |= {Index for CurveValue in Curves for Index in CurveValue.Poles}
    if not UsedRows.union(Table.Points) <= set(range(len(RowValues))):
        raise ValueError("Fusion Form stencil table names a missing row")
    return Table


@CacheValue
def ReadStencils() -> KMapping[str, StencilTable]:
    Source = ReadResources("convert.formats.Fusion.BrepCodec").joinpath(
        "Journal", "Spline", "Stencil", "FormStencils.xz"
    )
    Value = CastValue(StencilsJson, LoadJson(Decompress(Source.read_bytes())))
    Tables = [ReadTable(Entry) for Entry in Value["Tables"]]
    Keyed = {Table.LayoutKey: Table for Table in Tables}
    if len(Keyed) != len(Tables):
        raise ValueError("Fusion Form stencil tables repeat a cage layout")
    return ReadOnlyMap(Keyed)
