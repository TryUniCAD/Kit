import math
import sys
from pathlib import Path

sys.path.insert(0, "src")
from convert.adapters.catia.Container import CfvTwoArchive
from convert.adapters.catia.NativeBrep import (
    BrepData,
    CornerPositions,
    CornerUsage,
    Largest,
    ParseBrep,
    ParseSurfaces,
    SurfaceLimits,
    Violation,
)
from convert.adapters.catia.NativeSurface import AxisFromCarrier


def Dist(Point, Surface, Normal):
    if Surface.kind == 0x32:
        if Normal is None:
            return 0.0
        Origin = Surface.bounds[0:3]
        return abs(sum(Normal[I] * (Point[I] - Origin[I]) for I in range(3)))
    P = Surface.params
    if Surface.kind in (0x33, 0x34) and len(P) >= 6:
        Axis = AxisFromCarrier(P)
        Delta = [Point[I] - P[I] for I in range(3)]
        Along = sum(Delta[I] * Axis[I] for I in range(3))
        Radial = math.sqrt(max(0.0, sum(V * V for V in Delta) - Along**2))
        if Surface.kind == 0x33:
            return abs(Radial - abs(P[5]))
        return abs(Radial - abs(Along * math.tan(abs(P[5]))))
    if Surface.kind == 0x35 and len(P) >= 6:
        Delta = [Point[I] - P[I] for I in range(3)]
        return abs(math.sqrt(sum(V * V for V in Delta)) - abs(P[5]))
    return 0.0


def Load(Name):
    a = CfvTwoArchive.from_bytes(Path(f"re/catia/examples/.CATPart/{Name}.CATPart").read_bytes())
    Folder = a.nested[0]
    Pool = ParseSurfaces(a.stream_bytes(Largest(Folder, "SurfacicReps"), Folder))
    Brep = ParseBrep(a)
    Raw = [S.raw for S in Brep.surfaces]
    PoolRaw = [S.raw for S in Pool]
    Start = [PoolRaw.index(R) if R in PoolRaw else 0 for R in Raw]
    return Brep, Pool, Start


def Build(Brep, Pool, Assign):
    return BrepData(
        tuple(Pool[I] for I in Assign),
        Brep.trims,
        Brep.edges,
        Brep.vertices,
        Brep.roster,
        Brep.width,
        Brep.tessellation,
        True,
    )


def Measure(BrepValue):
    Usage = CornerUsage(BrepValue)[0]
    Pos = CornerPositions(BrepValue)
    Bad = 0
    Total = 0
    Worst = 0.0
    for Handle, Faces in Usage.items():
        Planes, Cyls = SurfaceLimits(BrepValue, Faces)
        Value = Violation(Pos[Handle], Planes, Cyls)
        Total += 1
        Worst = max(Worst, Value)
        if Value > 1e-3:
            Bad += 1
    return Bad, Total, Worst


def Refine(Brep, Pool, Assign, Rounds):
    Current = list(Assign)
    for RoundIndex in range(Rounds):
        BrepValue = Build(Brep, Pool, Current)
        Pos = CornerPositions(BrepValue)
        New = list(Current)
        for FaceIndex, Trim in enumerate(Brep.trims):
            Normal = Trim.vector
            BestIndex = Current[FaceIndex]
            BestCost = None
            for Index, Surface in enumerate(Pool):
                if Surface.kind != BrepValue.surfaces[FaceIndex].kind:
                    continue
                Cost = sum(Dist(Pos[H], Surface, Normal) for H in set(Trim.handles))
                if BestCost is None or Cost < BestCost - 1e-9:
                    BestCost = Cost
                    BestIndex = Index
            New[FaceIndex] = BestIndex
        Current = New
        Bad, Total, Worst = Measure(Build(Brep, Pool, Current))
        print(f"  round {RoundIndex}: unsatisfied {Bad}/{Total} worst {Worst:.4f}")
    return Current


for Name in sys.argv[1:]:
    print(f"=== {Name}")
    Brep, Pool, Start = Load(Name)
    Bad, Total, Worst = Measure(Build(Brep, Pool, Start))
    print(f"  start: unsatisfied {Bad}/{Total} worst {Worst:.4f} pool {len(Pool)} faces {len(Brep.trims)}")
    Refine(Brep, Pool, Start, 3)
