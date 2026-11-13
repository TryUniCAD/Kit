from __future__ import annotations

from .PadAttach import FindAttach


def BuildNotes(
    PointsMm: tuple[tuple[float, float], ...], DepthMm: float
) -> dict[int, float]:
    AttachmentX, AttachmentY = FindAttach(PointsMm)
    OutputData: dict[int, float] = {}
    for OffsetPos in (10044, 10068):
        OutputData[OffsetPos] = AttachmentX / 1000.0
    for OffsetPos in (10052, 10076):
        OutputData[OffsetPos] = AttachmentY / 1000.0
    OutputData[10241] = -AttachmentX / 1000.0
    OutputData[10257] = -AttachmentY / 1000.0
    OutputData[10330] = AttachmentX / 5000.0
    for OffsetPos in (10410, 10434):
        OutputData[OffsetPos] = -DepthMm / 1000.0
    return OutputData
