from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.GroupMateIn import (
    GroupMateIn,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Mates.CheckAsmMate import (
    CheckAsmMate,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Mates.ReadAsmEnd import (
    ReadAsmEnd,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Mates.ReadAsmLength import (
    ReadAsmLength,
)
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.Records.RecordParameter import Parameter


# each ordered relationship must bind both original endpoint records and its own optional driving length before construction
def ReadAsmRule(
    Value: MateConstraint,
    RootId: str,
    Entities: Mapping[str, MateEntity],
    Occurrences: Mapping[str, int],
    DatumAxes: Mapping[str, str],
    Parameters: Mapping[str, Parameter],
) -> GroupMateIn:
    CheckAsmMate(Value, RootId)
    First, Second = (
        ReadAsmEnd(Entities[Identity], RootId, Occurrences, DatumAxes)
        for Identity in Value.entity_ids
    )
    return GroupMateIn(
        str(Value.kind), Value.name, (First, Second), ReadAsmLength(Value, Parameters)
    )
