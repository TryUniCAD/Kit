from dataclasses import dataclass as DataClass


# one selected cylinder requires independently identified geometry and kernel and feature owners
@DataClass(frozen=True, slots=True)
class CylFaceBuild:
    OriginValue: tuple[float, float, float]
    AxisValue: tuple[float, float, float]
    RadiusValue: float
    RimCentres: tuple[tuple[float, float, float], tuple[float, float, float]]
    CapSelectors: tuple[tuple[int, int], tuple[int, int]]
    FeatureId: int
    CreatedAt: int
    ArcMarker: int
    FaceNodeId: int
    FaceTag: int
    BodyAtom: int
