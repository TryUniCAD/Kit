from __future__ import annotations


# principal frame expectations expose a reversed transform before the native loader can normalize it
def CheckFrame(PlaneAxis: str, Values: object) -> None:
    Matrix = {
        "x": [0, 0, 1, 0, 1, 0, -1, 0, 0],
        "y": [1, 0, 0, 0, 0, 1, 0, -1, 0],
        "z": [1, 0, 0, 0, 1, 0, 0, 0, 1],
    }[PlaneAxis]
    assert Values == [*Matrix, 0, 0, 0, 1]
