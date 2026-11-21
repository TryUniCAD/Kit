from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtStages import (
    ReadXmtStages,
)
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import (
    ReadBodyTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.CheckFilletDeps import (
    CheckFilletDeps,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.CheckFilletUndo import (
    CheckFilletUndo,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.CheckLiveRound import (
    CheckLiveRound,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletRad import (
    ReadFilletRad,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletOwn import (
    ReadFilletOwn,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletSlot import (
    ReadFilletSlot,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# cache and controller ownership must come from one complete ordinary part archive
def ReadFilletHist(ArchiveValue: SldprtArchive) -> FilletHistory:
    LinkValue = ReadNativeLink(ArchiveValue, 0, ReadFillets=True)
    OwnersValue = ReadFilletOwn(LinkValue)
    Selectors = tuple(
        FieldInt(Controller.FieldsValue, "f18")
        for Controller in OwnersValue.Controllers
    )
    Active, History = DecodePartData(
        ArchiveValue.require(KPartitionStream), KPartitionStream
    )
    NodesValue = ReadActiveNodes(Active.data)
    StagesValue = ReadXmtStages(History.data, NodesValue, Selectors)
    CheckFilletDeps(StagesValue)
    LiveBody, LiveName = ReadFilletSlot(
        NodesValue, OwnersValue.AtomValue, OwnersValue.FilletValue
    )
    Previous = StagesValue[1].NodesValue
    StockBody, StockName = ReadFilletSlot(
        Previous, OwnersValue.AtomValue, OwnersValue.StockValue
    )
    if ReadBodyTree(Previous).BodyIndex != StockBody.IndexValue:
        raise ValueError("SOLIDWORKS previous stock topology has a foreign owner")
    CheckFilletUndo(StagesValue, LiveBody, StockBody, LiveName, StockName)
    RadiusValue = ReadFilletRad(OwnersValue.FilletValue)
    CheckLiveRound(NodesValue, LiveBody, RadiusValue)
    return FilletHistory(OwnersValue, StagesValue, LiveBody.IndexValue, RadiusValue)
