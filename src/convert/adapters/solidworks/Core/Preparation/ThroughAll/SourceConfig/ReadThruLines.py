from convert.adapters.solidworks.Archive.Definition.LineTables.LineTableInput import (
    LineTableInput,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.ReadLineTables import (
    ReadLineTables,
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


# source line presentation remains subordinate to complete part and actual linked identity checks
def ReadThruLines(
    DocumentValue: CadDocument,
    LinkValue: NativeLink,
    DefinitionValue: ModelDefGraph,
) -> LineTableInput:
    CheckSourceEnv(DocumentValue)
    CheckThruLink(DocumentValue, LinkValue)
    return ReadLineTables(DefinitionValue)
