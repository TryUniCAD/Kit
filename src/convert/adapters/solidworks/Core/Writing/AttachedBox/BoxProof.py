from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import (
    AttachedBoxPlan,
)
from interchange.Enums.EnumDocument import Capability


# only the authenticated source graph can supply portable intent and its source evidence
@DataClass(frozen=True, slots=True)
class BoxProof:
    PlanValue: AttachedBoxPlan
    EvidenceValue: Mapping[str, object]
    NativeCaps: frozenset[Capability]
