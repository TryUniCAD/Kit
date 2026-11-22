from dataclasses import dataclass as DataClass


# neutral body binding requires the complete reachable kernel topology inventory
@DataClass(frozen=True, slots=True)
class BodyTree:
    BodyIndex: int
    FaceIds: tuple[int, ...]
    LoopIds: tuple[int, ...]
    FinIds: tuple[int, ...]
    EdgeIds: tuple[int, ...]
    VertexIds: tuple[int, ...]
    SurfaceIds: tuple[int, ...]
    CurveIds: tuple[int, ...]
    PointIds: tuple[int, ...]
