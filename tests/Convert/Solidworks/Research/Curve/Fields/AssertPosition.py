from __future__ import annotations

from typing import cast as CastValue


# optional object positions need bounded source ownership before correlation can use them
def AssertPosition(
    NodeData: dict[str, object], Streams: dict[str, dict[str, object]]
) -> None:
    PositionStream = NodeData["position_stream"]
    assert PositionStream is None or isinstance(PositionStream, str)
    StartValue, EndValue = NodeData["record_start"], NodeData["record_end"]
    if StartValue is None:
        assert PositionStream is None
    else:
        assert type(StartValue) is int and PositionStream in Streams
    for Position in (StartValue, EndValue):
        if Position is not None:
            assert type(Position) is int
            assert PositionStream is not None
            assert PositionStream in Streams
            assert 0 <= Position <= CastValue(int, Streams[PositionStream]["bytes"])
    if StartValue is not None and EndValue is not None:
        assert StartValue <= CastValue(int, EndValue)
