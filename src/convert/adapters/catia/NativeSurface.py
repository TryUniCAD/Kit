from __future__ import annotations

from dataclasses import dataclass
import math
import struct

from interchange import (
    CylinderSurface,
    NativeSurface,
    PlaneSurface,
    SpaceVector,
)

KSurfaceKinds = frozenset({0x32, 0x33, 0x34, 0x35, 0x38})
KSurfaceLens = {0x32: 49, 0x33: 73, 0x34: 73, 0x35: 65, 0x38: 77}
KBoundsOff = {0x32: 8, 0x33: 32, 0x34: 32, 0x35: 24, 0x38: 36}
KParamCount = {0x32: 0, 0x33: 6, 0x34: 6, 0x35: 4, 0x38: 7}


@dataclass(frozen=True, slots=True)
class SurfaceRec:
    kind: int
    offset: int
    params: tuple[float, ...]
    bounds: tuple[float, ...]
    sign: int
    raw: bytes


def Vector(Values: tuple[float, float, float]) -> SpaceVector:
    return SpaceVector(*Values)


def Normalize(Values: tuple[float, float, float]) -> tuple[float, float, float]:
    Length = math.sqrt(sum(Value * Value for Value in Values))
    if Length <= 1e-12:
        return (1.0, 0.0, 0.0)
    return (
        Values[0] / Length,
        Values[1] / Length,
        Values[2] / Length,
    )


def AxisFromBounds(Bounds: tuple[float, ...]) -> tuple[float, float, float]:
    Half = Bounds[3:6]
    Index = min(range(3), key=lambda Value: abs(Half[Value]))
    if Index == 0:
        return (1.0, 0.0, 0.0)
    if Index == 1:
        return (0.0, 1.0, 0.0)
    return (0.0, 0.0, 1.0)


def RefFromAxis(Axis: tuple[float, float, float]) -> tuple[float, float, float]:
    if abs(Axis[0]) < 0.9:
        return Normalize((1.0, 0.0, 0.0))
    return Normalize((0.0, 1.0, 0.0))


def ParseSurf(Data: bytes, Offset: int) -> tuple[SurfaceRec, int]:
    if Data[Offset + 2 : Offset + 4] != b"\x00\x33":
        raise ValueError("surface marker is missing")
    Kind = Data[Offset + 4]
    if Kind not in KSurfaceKinds:
        raise ValueError("surface kind is unsupported")
    Length = KSurfaceLens[Kind]
    Raw = Data[Offset : Offset + Length]
    Params = tuple(
        struct.unpack_from(">f", Raw, 8 + 4 * Index)[0]
        for Index in range(KParamCount[Kind])
    )
    Bounds = tuple(
        struct.unpack_from("<f", Raw, KBoundsOff[Kind] + 4 * Index)[0]
        for Index in range(10)
    )
    Sign = struct.unpack_from("b", Raw, Length - 1)[0]
    return SurfaceRec(Kind, Offset, Params, Bounds, Sign, Raw), Offset + Length


def MakeSurf(
    Rec: SurfaceRec, Index: int, VectorValue: tuple[float, float, float] | None
) -> object:
    SurfaceId = f"catia:surface:{Index}"
    Bounds = Rec.bounds
    Center = (Bounds[0], Bounds[1], Bounds[2])
    Axis = AxisFromBounds(Bounds)
    Ref = RefFromAxis(Axis)
    if Rec.kind == 0x32:
        Normal = Normalize(VectorValue) if VectorValue else Axis
        if all(math.isfinite(Value) for Value in (*Center, *Normal, *Ref)):
            return PlaneSurface(SurfaceId, Vector(Center), Vector(Normal), Vector(Ref))
    if Rec.kind == 0x33:
        Radius = max(Bounds[3:6])
        if math.isfinite(Radius) and Radius > 0.0:
            return CylinderSurface(
                SurfaceId, Vector(Center), Vector(Axis), Vector(Ref), Radius
            )
    return NativeSurface(
        SurfaceId,
        "catia.v5",
        f"surface-{Rec.kind:02x}",
        {"raw": Rec.raw.hex(), "bounds": Bounds},
    )
