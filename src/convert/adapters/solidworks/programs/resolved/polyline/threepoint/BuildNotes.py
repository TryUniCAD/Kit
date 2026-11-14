from __future__ import annotations

from .PadAttach import FindAttach


def BuildNotes(
    PointsMm: tuple[tuple[float, float], ...], DepthMm: float
) -> dict[int, float]:
    AttachmentX, AttachmentY = FindAttach(PointsMm)
    OutputData: dict[int, float] = {}
    for OffsetPos in (9440, 9464):
        OutputData[OffsetPos] = AttachmentX / 1000.0
    for OffsetPos in (9448, 9472):
        OutputData[OffsetPos] = AttachmentY / 1000.0
    OutputData[9637] = -AttachmentX / 1000.0
    OutputData[9653] = -AttachmentY / 1000.0
    OutputData[9726] = AttachmentX / 5000.0
    for OffsetPos in (9806, 9830):
        OutputData[OffsetPos] = -DepthMm / 1000.0
    return OutputData
