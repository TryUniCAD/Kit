from math import pi as PiValue

from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields, SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    NumberValue,
    ObjectFields,
    PointCoords,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# cached circular geometry must identify the preceding top rim rather than a plausible final edge
def CheckRimCircle(Graph: NativeGraph, Context: RimContext, Cache: NativeNode) -> None:
    RequireFields(
        Cache,
        {
            "progenitor": None,
            "rCachedEdge": None,
            "startPtProgenitor": None,
            "endPtProgenitor": None,
        },
    )
    CheckIdentity(Cache.Fields["sketchTransf"])
    Geometry = ObjectFields(Cache.Fields["rCachedGeometry"])
    if set(Geometry) != {
        "center",
        "normal",
        "refVec",
        "radius",
        "startAngle",
        "endAngle",
    }:
        raise ValueError("Native rim cached circle has unknown semantic members")
    SameNumbers(
        PointCoords(Geometry["center"]),
        (0, 0, NumberValue(Context.Extrusion.Along.Fields["value"])),
    )
    SameNumbers(PointCoords(Geometry["normal"]), (0, 0, 1))
    SameNumbers(PointCoords(Geometry["refVec"]), (1, 0, 0))
    SameNumbers(
        (
            NumberValue(Geometry["radius"]),
            NumberValue(Geometry["startAngle"]),
            NumberValue(Geometry["endAngle"]),
        ),
        (ReadCircle(Graph, Context.Extrusion).Geometry.radius / 10, 0, 2 * PiValue),
    )
