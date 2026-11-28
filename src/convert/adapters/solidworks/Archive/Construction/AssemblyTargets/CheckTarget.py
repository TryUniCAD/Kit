from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.CheckTargetRoot import (
    CheckTargetRoot,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.CheckTargetRows import (
    CheckTargetRows,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)


# recursive generation must preserve a finite acyclic actual definition graph while allowing one generated target to serve repeated placements
def CheckTarget(TargetValue: TargetDocument) -> None:
    Pending: list[tuple[TargetDocument, bool]] = [(TargetValue, False)]
    ActiveValues: set[int] = set()
    SeenValues: set[int] = set()
    while Pending:
        CurrentValue, IsLeaving = Pending.pop()
        if type(CurrentValue) is not TargetDocument:
            raise TypeError("placement requires an actual generated target descriptor")
        IdentityValue = id(CurrentValue.RootValue)
        if IsLeaving:
            ActiveValues.remove(IdentityValue)
            SeenValues.add(IdentityValue)
            continue
        if IdentityValue in ActiveValues:
            raise ValueError("generated target definition graph contains a cycle")
        CheckTargetRoot(CurrentValue)
        CheckTargetRows(CurrentValue)
        if IdentityValue not in SeenValues:
            ActiveValues.add(IdentityValue)
            Pending.append((CurrentValue, True))
            Pending.extend(
                (ChildValue, False)
                for ChildValue in reversed(CurrentValue.ChildTargets)
            )
