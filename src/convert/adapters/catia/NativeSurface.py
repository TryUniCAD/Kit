from __future__ import annotations

from dataclasses import dataclass
import math
import struct

from interchange import (
    BrepSurface,
    CylinderSurface,
    NativeSurface,
    PlaneSurface,
    SpaceVector,
)

# this binding exists because shared behavior needs one stable value
KSurfaceKinds = frozenset({0x32, 0x33, 0x34, 0x35, 0x38})

# this binding exists because shared behavior needs one stable value
KSurfaceLens = {0x32: 49, 0x33: 73, 0x34: 73, 0x35: 65, 0x38: 77}

# this binding exists because shared behavior needs one stable value
KBoundsOff = {0x32: 8, 0x33: 32, 0x34: 32, 0x35: 24, 0x38: 36}

# this binding exists because shared behavior needs one stable value
KParamCount = {0x32: 0, 0x33: 6, 0x34: 6, 0x35: 4, 0x38: 7}


# this definition exists because focused behavior needs one stable owner
@dataclass(frozen=True, slots=True)
class SurfaceRec:
    kind: int
    offset: int
    params: tuple[float, ...]
    bounds: tuple[float, ...]
    sign: int
    raw: bytes


# this definition exists because focused behavior needs one stable owner
def Vector(Values: tuple[float, float, float]) -> SpaceVector:
    return SpaceVector(*Values)


# this definition exists because focused behavior needs one stable owner
def Normalize(Values: tuple[float, float, float]) -> tuple[float, float, float]:
    Length = math.sqrt(sum(Value * Value for Value in Values))
    if Length <= 1e-12:
        return (1.0, 0.0, 0.0)
    return (
        Values[0] / Length,
        Values[1] / Length,
        Values[2] / Length,
    )


# this definition exists because focused behavior needs one stable owner
def AxisFromBounds(Bounds: tuple[float, ...]) -> tuple[float, float, float]:
    HalfExtent = Bounds[3:6]
    Index = min(range(3), key=lambda Value: abs(HalfExtent[Value]))
    if Index == 0:
        return (1.0, 0.0, 0.0)
    if Index == 1:
        return (0.0, 1.0, 0.0)
    return (0.0, 0.0, 1.0)


# this definition exists because focused behavior needs one stable owner
def RefFromAxis(AxisValue: tuple[float, float, float]) -> tuple[float, float, float]:
    if abs(AxisValue[0]) < 0.9:
        return Normalize((1.0, 0.0, 0.0))
    return Normalize((0.0, 1.0, 0.0))


# this definition exists because focused behavior needs one stable owner
def ParseSurf(SourceData: bytes, Offset: int) -> tuple[SurfaceRec, int]:
    if SourceData[Offset + 2 : Offset + 4] != b"\x00\x33":
        raise ValueError("surface marker is missing")
    KindValue = SourceData[Offset + 4]
    if KindValue not in KSurfaceKinds:
        raise ValueError("surface kind is unsupported")
    Length = KSurfaceLens[KindValue]
    RawBytes = SourceData[Offset : Offset + Length]
    Params = tuple(
        struct.unpack_from(">f", RawBytes, 8 + 4 * Index)[0]
        for Index in range(KParamCount[KindValue])
    )
    Bounds = tuple(
        struct.unpack_from("<f", RawBytes, KBoundsOff[KindValue] + 4 * Index)[0]
        for Index in range(10)
    )
    SignValue = struct.unpack_from("b", RawBytes, Length - 1)[0]
    return (
        SurfaceRec(KindValue, Offset, Params, Bounds, SignValue, RawBytes),
        Offset + Length,
    )


# this definition exists because focused behavior needs one stable owner
def MakeSurf(
    RecordValue: SurfaceRec,
    Index: int,
    VectorValue: tuple[float, float, float] | None,
) -> BrepSurface:
    SurfaceId = f"catia:surface:{Index}"
    Bounds = RecordValue.bounds
    Center = (Bounds[0], Bounds[1], Bounds[2])
    AxisValue = AxisFromBounds(Bounds)
    RefValue = RefFromAxis(AxisValue)
    if RecordValue.kind == 0x32:
        Normal = Normalize(VectorValue) if VectorValue else AxisValue
        if all(math.isfinite(Value) for Value in (*Center, *Normal, *RefValue)):
            return PlaneSurface(
                SurfaceId, Vector(Center), Vector(Normal), Vector(RefValue)
            )
    if RecordValue.kind == 0x33:
        Radius = max(Bounds[3:6])
        if math.isfinite(Radius) and Radius > 0.0:
            return CylinderSurface(
                SurfaceId, Vector(Center), Vector(AxisValue), Vector(RefValue), Radius
            )
    return NativeSurface(
        SurfaceId,
        "catia.v5",
        f"surface-{RecordValue.kind:02x}",
        {"raw": RecordValue.raw.hex(), "bounds": Bounds},
    )
