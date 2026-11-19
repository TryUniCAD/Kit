from convert.adapters.solidworks.Archive.Construction.Configuration.Events.CmgrEvents import (
    CmgrEvents,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.Events.RequireCmgr import (
    RequireCmgr,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.CheckSourceEnv import (
    CheckSourceEnv,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.CheckThruLink import (
    CheckThruLink,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.Events.ReadCfgEvent import (
    ReadCfgEvent,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.document.Models.DocumentModel import CadDocument


# the source projection uses the actual directory selection while the caller retains same archive custody
def ReadThruEvents(
    DocumentValue: CadDocument, LinkValue: NativeLink, ManagerValue: ArchiveNode
) -> CmgrEvents:
    CheckSourceEnv(DocumentValue)
    CheckThruLink(DocumentValue, LinkValue)
    ActiveValue = RequireCmgr(ManagerValue)
    if DocumentValue.configurations[0].name != ReadNodeName(ActiveValue):
        raise ValueError("source configuration differs from the actual selected owner")
    return CmgrEvents(ReadCfgEvent(ManagerValue), ReadCfgEvent(ActiveValue))
