from __future__ import annotations

from .PadGeometry import AttachmentPoint, PadBounds


def BoundingMap(Bounds: PadBounds) -> dict[int, float]:
    OutputData: dict[int, float] = {}
    for OffsetPos in (8797, 9027):
        OutputData[OffsetPos] = Bounds.centre_x
    for OffsetPos in (8805, 9035):
        OutputData[OffsetPos] = Bounds.centre_y
    for OffsetPos in (8813, 9043, 4309, 4879):
        OutputData[OffsetPos] = Bounds.centre_z
    for OffsetPos in (8821, 9051):
        OutputData[OffsetPos] = Bounds.diameter
    return OutputData


def DisplayMap(Bounds: PadBounds) -> dict[int, float]:
    OutputData: dict[int, float] = {}
    for OffsetPos in (3533, 4052):
        OutputData[OffsetPos] = Bounds.centre_x - Bounds.expanded_x
    for OffsetPos in (3541, 4630):
        OutputData[OffsetPos] = Bounds.centre_y + Bounds.expanded_y
    for OffsetPos in (3680, 4246):
        OutputData[OffsetPos] = Bounds.expanded_x
    for OffsetPos in (3688, 4254):
        OutputData[OffsetPos] = -Bounds.expanded_x
    for OffsetPos in (3696, 4832):
        OutputData[OffsetPos] = Bounds.expanded_y
    for OffsetPos in (3704, 4840):
        OutputData[OffsetPos] = -Bounds.expanded_y
    for OffsetPos in (3727, 4293):
        OutputData[OffsetPos] = Bounds.centre_x
    for OffsetPos in (3735, 4871):
        OutputData[OffsetPos] = Bounds.centre_y
    for OffsetPos in (4309, 4879):
        OutputData[OffsetPos] = Bounds.centre_z
    OutputData[4068] = Bounds.centre_z - Bounds.expanded_z
    OutputData[4638] = Bounds.centre_z + Bounds.expanded_z
    for OffsetPos in (4262, 4816):
        OutputData[OffsetPos] = Bounds.expanded_z
    for OffsetPos in (4270, 4824):
        OutputData[OffsetPos] = -Bounds.expanded_z
    return OutputData


def AnnotationMap(
    PointsMm: tuple[tuple[float, float], ...], DepthMm: float
) -> dict[int, float]:
    AttachmentX, AttachmentY = AttachmentPoint(PointsMm)
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
