from convert.adapters.solidworks.Archive.Definition.EmptyManagers.EmptyMgrInput import (
    EmptyMgrInput,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.MakeAppearMgr import (
    MakeAppearMgr,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.MakeBomMgr import (
    MakeBomMgr,
)


# each empty manager derives its own native presence representation from the semantic state
def MakeEmptyMgrs(InputValue: EmptyMgrInput) -> dict[str, object]:
    if type(InputValue) is not EmptyMgrInput:
        raise TypeError("empty model managers require typed semantic input")
    return {"fab8": MakeBomMgr(InputValue.BomOnWire)} | MakeAppearMgr(
        InputValue.AppearanceValue
    )
