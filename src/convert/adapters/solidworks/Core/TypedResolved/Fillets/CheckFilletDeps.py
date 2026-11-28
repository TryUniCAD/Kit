from convert.adapters.solidworks.Archive.Partition.History.XmtStage import XmtStage
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences


# every live and restored owner must be reachable from the world or its stable attribute registry
def CheckFilletDeps(StagesValue: tuple[XmtStage, ...]) -> None:
    Active = StagesValue[0].NodesValue
    WorldValue = RequireXmt(Active, 1, 101)
    Definitions = WalkXmtChain(
        Active, WorldValue.Integer("attrib_def"), 80, PreviousField=None
    )
    Registry = {
        *Definitions,
        *(Active[IndexValue].Integer("identifier") for IndexValue in Definitions),
    }
    if Registry != {
        IndexValue
        for IndexValue, NodeValue in Active.items()
        if NodeValue.KindValue in (79, 80)
    }:
        raise ValueError("SOLIDWORKS fillet history has a foreign attribute registry")
    for StageValue in StagesValue:
        NodesValue = StageValue.NodesValue
        if any(
            NodesValue.get(IndexValue) is not Active[IndexValue]
            for IndexValue in Registry
        ):
            raise ValueError(
                "SOLIDWORKS fillet rollback changes the global attribute registry"
            )
        Pending = {1, *Registry}
        SeenValue: set[int] = set()
        while Pending:
            IndexValue = Pending.pop()
            SeenValue.add(IndexValue)
            Pending.update(set(XmtReferences(NodesValue[IndexValue])) - SeenValue)
        if SeenValue != set(NodesValue):
            raise ValueError("SOLIDWORKS fillet rollback has a detached owner")
