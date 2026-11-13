from struct import pack as PackFields
from sys import float_info as FloatInfo
from uuid import UUID

KPointTriple = tuple[float, float, float]
KStateLead = bytes(18)
KStateMark = bytes.fromhex("2184de7b09")
KStateTail = bytes.fromhex("9101")
KStateKind = 2
KEmptyBox = (FloatInfo.max, FloatInfo.max, -FloatInfo.max, -FloatInfo.max)


def GuidBytes(GuidText: str) -> bytes:
    try:
        return UUID(GuidText).bytes_le
    except ValueError as Failure:
        raise ValueError(
            f"Authored DWG view GUID {GuidText!r} is malformed"
        ) from Failure


def ViewState(
    Target: KPointTriple,
    EyeAxis: KPointTriple,
    UpAxis: KPointTriple,
    GeometryGuid: str,
    Extent: KPointTriple,
) -> bytes:
    return b"".join(
        (
            KStateLead,
            PackFields("<3d", *Target),
            PackFields("<3d", *EyeAxis),
            PackFields("<3d", *UpAxis),
            b"\x01",
            PackFields("<d", 0.0),
            b"\x00",
            PackFields("<q", KStateKind),
            GuidBytes(GeometryGuid),
            PackFields("<3d", 0.0, 0.0, 0.0),
            PackFields("<3d", *Extent),
            KStateMark,
            PackFields("<d", 0.0),
            PackFields("<4d", *KEmptyBox),
            KStateTail,
        )
    )
