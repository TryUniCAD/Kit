from dataclasses import dataclass as MakeDataClass
from typing import Literal

# the source child map names only these boundary classes
KBoxKind = Literal["edge", "face", "vertex"]


# each indexed body entity needs one qualified shape creator and neutral identity
@MakeDataClass(frozen=True, slots=True)
class BoxElement:
    KindValue: KBoxKind
    BodyOrdinal: int
    ChildOrdinal: int
    EntityId: str
    BoundaryRole: str


# document identity scopes the native aliases independently of local shape ids
@MakeDataClass(frozen=True, slots=True)
class BoxLineage:
    SourceSha256: str
    DocumentUuid: str
    BodyXmlId: int
    ChildXmlId: int
    BodyId: str
    ProducerId: str
    BodyShapeId: str
    ChildShapeId: str
    MapSha256: str
    Elements: tuple[BoxElement, ...]
