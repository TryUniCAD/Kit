from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.History.XmtStage import XmtStage
from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletOwners import (
    FilletOwners,
)


# qualified fillet history must expose restored topology alongside its controller provenance
@DataClass(frozen=True, slots=True)
class FilletHistory:
    OwnersValue: FilletOwners
    StagesValue: tuple[XmtStage, ...]
    BodyIndex: int
    RadiusValue: float
