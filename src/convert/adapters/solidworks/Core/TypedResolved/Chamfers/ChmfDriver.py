from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# angle and distance each preserve a complete chain back to the actual archived driver
@DataClass(frozen=True, slots=True)
class ChmfDriver:
    NameValue: str
    ValueSi: float
    DisplayNode: ArchiveNode
    HandleNode: ArchiveNode
    DimensionNode: ArchiveNode
    ParameterNode: ArchiveNode
