from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.CheckTargetRoot import (
    CheckTargetRoot,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.CheckTargetRows import (
    CheckTargetRows,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetAudit import (
    TargetAudit,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)


# recursive generation must preserve a finite acyclic actual definition graph while allowing one generated target to serve repeated placements
def CheckTargetMut(TargetValue: TargetDocument, AuditValue: TargetAudit) -> None:
    Pending: list[tuple[TargetDocument, bool]] = [(TargetValue, False)]
    ActiveValues: set[int] = set()
    while Pending:
        CurrentValue, IsLeaving = Pending.pop()
        if type(CurrentValue) is not TargetDocument:
            raise TypeError("placement requires an actual generated target descriptor")
        IdentityValue = id(CurrentValue.RootValue)
        if IsLeaving:
            ActiveValues.remove(IdentityValue)
            AuditValue.StoreTargetMut(CurrentValue)
            continue
        if IdentityValue in ActiveValues:
            raise ValueError("generated target definition graph contains a cycle")
        if id(CurrentValue) in AuditValue.Targets:
            continue
        CheckTargetRoot(CurrentValue)
        CheckTargetRows(CurrentValue)
        ActiveValues.add(IdentityValue)
        Pending.append((CurrentValue, True))
        Pending.extend(
            (ChildValue, False) for ChildValue in reversed(CurrentValue.ChildTargets)
        )
