from dataclasses import dataclass as DataClass


# planar selections retain numeric occurrence and datum identities across neutral translation
@DataClass(frozen=True, slots=True)
class PlanarEndpoint:
    OccurrenceFeatureId: int
    OccurrenceObjectId: int
    ChildDefinitionId: int
    ChildConfigId: int
    ChildUpdateStamp: int
    DatumFeatureId: int
    DatumName: str
    OriginValue: tuple[float, float, float]
    NormalValue: tuple[float, float, float]
