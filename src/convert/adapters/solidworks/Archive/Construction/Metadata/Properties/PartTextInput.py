from collections.abc import Mapping
from dataclasses import dataclass as DataClass


# neutral part text belongs to three independent owners with independent namespaces
@DataClass(frozen=True, slots=True)
class PartTextInput:
    SummaryFields: Mapping[str, object]
    DocumentFields: Mapping[str, object]
    ConfigurationFields: Mapping[str, object]
    EmptyScopes: frozenset[str] = frozenset()
    HasEmptyFileOwner: bool = False
