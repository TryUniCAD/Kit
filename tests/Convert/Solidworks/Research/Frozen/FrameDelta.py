from __future__ import annotations

from convert.adapters.solidworks.Container.Container import SldprtArchive


# transform correction must be present in the decoded model without changing unrelated generated streams
def FrameDelta(
    CurrentBytes: bytes, PriorBytes: bytes, PlaneAxis: str, Values: object
) -> list[str]:
    Matrix = {
        "x": [0, 0, 1, 0, 1, 0, -1, 0, 0],
        "y": [1, 0, 0, 0, 0, 1, 0, -1, 0],
        "z": [1, 0, 0, 0, 1, 0, 0, 0, 1],
    }[PlaneAxis]
    assert Values == [*Matrix, 0, 0, 0, 1]
    if PlaneAxis == "z":
        assert CurrentBytes == PriorBytes
        return []
    Current = SldprtArchive.FromBytes(CurrentBytes)
    Historic = SldprtArchive.FromBytes(PriorBytes)
    assert Current.format_version == Historic.format_version
    assert Current.file_id == Historic.file_id
    CurrentStreams, PriorStreams = Current.Streams, Historic.Streams
    assert tuple(CurrentStreams) == tuple(PriorStreams)
    assert all(
        len(Payload) == len(PriorStreams[NameValue])
        for NameValue, Payload in CurrentStreams.items()
    )
    Changed = [
        NameValue
        for NameValue, Payload in CurrentStreams.items()
        if Payload != PriorStreams[NameValue]
    ]
    assert Changed == ["Contents/Config-0-ResolvedFeatures"]
    return Changed
