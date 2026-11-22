from collections.abc import Mapping
from dataclasses import dataclass as DataClass


# the public binding needs the proven configuration and distinct native expression identities together
@DataClass(frozen=True, slots=True)
class WidthDepthLink:
    SourceText: str
    RightText: str
    WidthFeature: int
    DepthFeature: int
    RelationOwner: Mapping[str, object]
    WidthOwner: Mapping[str, object]
    DepthOwner: Mapping[str, object]

    # related provenance documents the distinct physical expression target and dependency owners
    @property
    def EvidenceValue(self) -> Mapping[str, object]:
        return {
            "relation": self.RelationOwner,
            "target": self.DepthOwner,
            "dependency": self.WidthOwner,
        }
