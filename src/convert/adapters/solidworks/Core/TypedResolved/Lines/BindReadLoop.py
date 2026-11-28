from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeProfile, NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineNativeDims import (
    LineNativeDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop


# both admitted loop kinds project their typed geometry and erase speculative legacy dimensions
def BindReadLoop(Sketch: NativeSketch, LoopValue: LineLoop) -> NativeSketch:
    return ReplaceValue(
        Sketch,
        TypedLines=LoopValue,
        profiles=(
            NativeProfile(
                "line-loop",
                tuple(
                    Coordinate
                    for Point in LoopValue.PointsValue
                    for Coordinate in Point.PositionValue
                ),
                (),
            ),
        ),
        dimensions=LineNativeDims(LoopValue.DimsValue),
        constraints=(),
    )
