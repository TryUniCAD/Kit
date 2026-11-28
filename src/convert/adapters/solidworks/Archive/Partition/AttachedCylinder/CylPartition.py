from dataclasses import dataclass as DataClass


# the attached feature must consume the same retained kernel objects as the assembly selector
@DataClass(frozen=True, slots=True)
class CylPartition:
    BytesValue: bytes
    BodyTag: int
    FaceTag: int
    ActivationId: int
    SelectedId: int
