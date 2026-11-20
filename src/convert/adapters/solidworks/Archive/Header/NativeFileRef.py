from dataclasses import dataclass as DataClass


# directory entries identify external files independently from configuration references
@DataClass(frozen=True, slots=True)
class NativeFileRef:
    PathValue: str
    NameValue: str
    KindValue: int
    ConfigValue: str
