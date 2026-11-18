from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)


# each placement must retain its actual generated definition separately from the independently authored occurrence frame and name
@DataClass(frozen=True, slots=True)
class TargetPlacement:
    TargetValue: TargetDocument
    OccurrenceValue: OccurrenceIn

    # typed placements prevent foreign descriptors or unvalidated occurrence records from entering recursive publication
    def __post_init__(self) -> None:
        if (
            type(self.TargetValue) is not TargetDocument
            or type(self.OccurrenceValue) is not OccurrenceIn
        ):
            raise TypeError(
                "recursive placement requires an actual generated target and typed occurrence"
            )
