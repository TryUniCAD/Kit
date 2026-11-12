from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.MeshStreams import MeshStreams


def FinishStreams(State: MeshStreams) -> tuple[GraphicsStream, ...]:
    Results: list[GraphicsStream] = []
    if State.IsReading and set(State.Inputs) != set(State.Ranges):
        raise ValueError("Unreferenced graphics mesh streams")
    for Stream, Ranges in sorted(State.Ranges.items()):
        Output = bytearray()
        for (Start, _), Payload in sorted(Ranges.items()):
            if Start != len(Output):
                raise ValueError("Unaccounted graphics mesh bytes")
            Output.extend(Payload)
        if State.IsReading and len(Output) != len(State.Inputs[Stream]):
            raise ValueError("Trailing graphics mesh bytes")
        Results.append(GraphicsStream(Stream, bytes(Output)))
    return tuple(Results)
