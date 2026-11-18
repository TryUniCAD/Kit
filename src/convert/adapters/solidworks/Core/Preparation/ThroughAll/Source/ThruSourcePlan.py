from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ThruSourceEnv import (
    ThruSourceEnv,
)


# source awareness requires the executable portable owners and the complete unqualified envelope to travel together
@DataClass(frozen=True, slots=True)
class ThruSourcePlan:
    InputValue: ThruOwnerInput
    EnvelopeValue: ThruSourceEnv
