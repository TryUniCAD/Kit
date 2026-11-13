from dataclasses import dataclass as MakeDataClass

KPointTriple = tuple[float, float, float]


@MakeDataClass(frozen=True, slots=True)
class ViewSource:
    BodyId: int
    ComponentText: str
    GeometryGuid: str
    BoundsMin: KPointTriple
    BoundsMax: KPointTriple
    MaterialText: str = ""
