from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Definition.PartUi.PartUiInput import (
    PartUiInput,
)
from convert.adapters.solidworks.Archive.Definition.PartUi.ReadPartUi import ReadPartUi
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.CheckSourceEnv import (
    CheckSourceEnv,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.CheckThruLink import (
    CheckThruLink,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.document.Models.DocumentModel import CadDocument


# source view preferences remain subordinate to actual part linkage and the unchanged complete source refusal
def ReadThruUi(
    DocumentValue: CadDocument,
    LinkValue: NativeLink,
    DefinitionValue: ModelDefGraph,
) -> PartUiInput:
    CheckSourceEnv(DocumentValue)
    CheckThruLink(DocumentValue, LinkValue)
    return ReadPartUi(DefinitionValue)
