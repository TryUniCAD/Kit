from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from typing import cast as CastValue

from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# every retained typed reference must resolve even when it is not a projected feature parameter
def CheckRimRef(Value: object, Graph: NativeGraph, SegmentId: int) -> None:
    if isinstance(Value, (LocalRef, SegmentRef)):
        _ = Graph.Resolve(Value, SegmentId)
    elif IsDataClass(Value) and not isinstance(Value, type):
        for Field in DataFields(Value):
            CheckRimRef(getattr(Value, Field.name), Graph, SegmentId)
    elif isinstance(Value, tuple):
        for Entry in CastValue(tuple[object, ...], Value):
            CheckRimRef(Entry, Graph, SegmentId)
