from convert.adapters.solidworks.Archive.Definition.EmptyManagers.EmptyMgrInput import (
    EmptyMgrInput,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.ReadEmptyMgrs import (
    ReadEmptyMgrs,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.CheckSourceEnv import (
    CheckSourceEnv,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.CheckThruLink import (
    CheckThruLink,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.document.Models.DocumentModel import CadDocument


# source empty managers must be read only after the retained part and actual linked feature inventory agree
def ReadThruMgrs(
    DocumentValue: CadDocument,
    LinkValue: NativeLink,
    DefinitionValue: ModelDefGraph,
) -> EmptyMgrInput:
    CheckSourceEnv(DocumentValue)
    CheckThruLink(DocumentValue, LinkValue)
    return ReadEmptyMgrs(DefinitionValue)
