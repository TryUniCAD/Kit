from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.Native import NativeFeature


# timeline changes and their separately qualified native presentation evidence must be returned atomically
@DataClass(frozen=True, slots=True)
class TreeProjection:
    FeaturesValue: tuple[NativeFeature, ...]
    EvidenceValue: Mapping[str, object]
