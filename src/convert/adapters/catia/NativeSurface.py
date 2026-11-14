from __future__ import annotations

from dataclasses import dataclass
import math
import struct

from interchange import (
    BrepSurface,
    ConeSurface,
    CylinderSurface,
    NativeSurface,
    PlaneSurface,
    SphereSurface,
    SpaceVector,
    TorusSurface,
)

# this binding exists because shared behavior needs one stable value
KSurfaceKinds = frozenset({0x32, 0x33, 0x34, 0x35, 0x38})

# this binding exists because shared behavior needs one stable value
KSurfaceLens = {0x32: 49, 0x33: 73, 0x34: 73, 0x35: 65, 0x38: 77}

# this binding exists because shared behavior needs one stable value
KCarrierCount = {0x32: 0, 0x33: 6, 0x34: 6, 0x35: 4, 0x38: 7}


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
def RefFromAxis(AxisValue: tuple[float, float, float]) -> tuple[float, float, float]:
    if abs(AxisValue[0]) < 0.9:
        return Normalize((1.0, 0.0, 0.0))
    return Normalize((0.0, 1.0, 0.0))


# this definition exists because focused behavior needs one stable owner
def AxisFromCarrier(Params: tuple[float, ...]) -> tuple[float, float, float]:
    AxisX = Params[3]
    AxisY = Params[4]
    AxisZ = math.sqrt(max(0.0, 1.0 - AxisX * AxisX - AxisY * AxisY))
    return Normalize((AxisX, AxisY, AxisZ))


# this definition exists because focused behavior needs one stable owner
def ParseSurf(SourceData: bytes, Offset: int) -> tuple[SurfaceRec, int]:
    if SourceData[Offset + 2 : Offset + 4] != b"\x00\x33":
        raise ValueError("surface marker is missing")
    KindValue = SourceData[Offset + 4]
    if KindValue not in KSurfaceKinds:
        raise ValueError("surface kind is unsupported")
    Length = KSurfaceLens[KindValue]
    RawBytes = SourceData[Offset : Offset + Length]
    CarrierCount = KCarrierCount[KindValue]
    Params = tuple(
        struct.unpack_from(">f", RawBytes, 5 + 4 * Index)[0]
        for Index in range(CarrierCount)
    )
    BoundsOffset = 5 + 4 * CarrierCount
    Bounds = tuple(
        struct.unpack_from("<f", RawBytes, BoundsOffset + 4 * Index)[0]
        for Index in range(10)
    )
    SignValue = struct.unpack_from("b", RawBytes, Length - 4)[0]
    return (
        SurfaceRec(KindValue, Offset, Params, Bounds, SignValue, RawBytes),
        Offset + Length,
    )


# this definition exists because focused behavior needs one stable owner
def BoundsNormal(Bounds: tuple[float, ...]) -> tuple[float, float, float]:
    HalfExtent = Bounds[3:6]
    Index = min(range(3), key=lambda Value: abs(HalfExtent[Value]))
    if Index == 0:
        return (1.0, 0.0, 0.0)
    if Index == 1:
        return (0.0, 1.0, 0.0)
    return (0.0, 0.0, 1.0)


# this definition exists because focused behavior needs one stable owner
def MakePlane(
    SurfaceId: str,
    RecordValue: SurfaceRec,
    VectorValue: tuple[float, float, float] | None,
) -> BrepSurface | None:
    Bounds = RecordValue.bounds
    Center = (Bounds[0], Bounds[1], Bounds[2])
    Normal = Normalize(VectorValue) if VectorValue else BoundsNormal(Bounds)
    RefValue = RefFromAxis(Normal)
    if not all(math.isfinite(Value) for Value in (*Center, *Normal, *RefValue)):
        return None
    return PlaneSurface(SurfaceId, Vector(Center), Vector(Normal), Vector(RefValue))


# this definition exists because focused behavior needs one stable owner
def MakeCylinder(SurfaceId: str, Params: tuple[float, ...]) -> BrepSurface | None:
    if len(Params) < 6:
        return None
    AxisValue = AxisFromCarrier(Params)
    Radius = abs(Params[5])
    if not math.isfinite(Radius) or Radius <= 0.0:
        return None
    return CylinderSurface(
        SurfaceId,
        Vector((Params[0], Params[1], Params[2])),
        Vector(AxisValue),
        Vector(RefFromAxis(AxisValue)),
        Radius,
    )


# this definition exists because focused behavior needs one stable owner
def MakeCone(SurfaceId: str, Params: tuple[float, ...]) -> BrepSurface | None:
    if len(Params) < 6:
        return None
    AxisValue = AxisFromCarrier(Params)
    HalfAngle = abs(Params[5])
    if not math.isfinite(HalfAngle) or not 0.0 < HalfAngle < math.pi / 2.0:
        return None
    return ConeSurface(
        SurfaceId,
        Vector((Params[0], Params[1], Params[2])),
        Vector(AxisValue),
        Vector(RefFromAxis(AxisValue)),
        0.0,
        HalfAngle,
    )


# this definition exists because focused behavior needs one stable owner
def MakeSphere(SurfaceId: str, Params: tuple[float, ...]) -> BrepSurface | None:
    if len(Params) < 4:
        return None
    Radius = abs(Params[3])
    if not math.isfinite(Radius) or Radius <= 0.0:
        return None
    return SphereSurface(
        SurfaceId,
        Vector((Params[0], Params[1], Params[2])),
        Vector((0.0, 0.0, 1.0)),
        Vector((1.0, 0.0, 0.0)),
        Radius,
    )


# this definition exists because focused behavior needs one stable owner
def MakeTorus(SurfaceId: str, Params: tuple[float, ...]) -> BrepSurface | None:
    if len(Params) < 7:
        return None
    AxisValue = AxisFromCarrier(Params)
    Major = abs(Params[5])
    Minor = abs(Params[6])
    if not math.isfinite(Major) or not math.isfinite(Minor) or Major <= 0.0:
        return None
    return TorusSurface(
        SurfaceId,
        Vector((Params[0], Params[1], Params[2])),
        Vector(AxisValue),
        Vector(RefFromAxis(AxisValue)),
        Major,
        Minor,
    )


# this definition exists because focused behavior needs one stable owner
def MakeSurf(
    RecordValue: SurfaceRec,
    Index: int,
    VectorValue: tuple[float, float, float] | None,
) -> BrepSurface:
    SurfaceId = f"catia:surface:{Index}"
    Params = RecordValue.params
    Builders = {
        0x32: lambda: MakePlane(SurfaceId, RecordValue, VectorValue),
        0x33: lambda: MakeCylinder(SurfaceId, Params),
        0x34: lambda: MakeCone(SurfaceId, Params),
        0x35: lambda: MakeSphere(SurfaceId, Params),
        0x38: lambda: MakeTorus(SurfaceId, Params),
    }
    Builder = Builders.get(RecordValue.kind)
    if Builder is not None:
        SurfaceValue = Builder()
        if SurfaceValue is not None:
            return SurfaceValue
    return NativeSurface(
        SurfaceId,
        "catia.v5",
        f"surface-{RecordValue.kind:02x}",
        {"raw": RecordValue.raw.hex(), "bounds": RecordValue.bounds},
    )
