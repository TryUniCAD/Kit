from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Views.ReadViewPair import ReadViewPair
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.CheckSourceEnv import (
    CheckSourceEnv,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.CheckThruLink import (
    CheckThruLink,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.document.Models.DocumentModel import CadDocument


# source camera projection retains complete part admission checks while isolating the two proven document view owners
def ReadThruView(
    DocumentValue: CadDocument,
    LinkValue: NativeLink,
    DefinitionValue: ModelDefGraph,
) -> ViewInput:
    CheckSourceEnv(DocumentValue)
    CheckThruLink(DocumentValue, LinkValue)
    if (
        type(DefinitionValue) is not ModelDefGraph
        or DefinitionValue.VersionValue != 19000
        or DefinitionValue.DocumentValue.ClassValue != RuntimeClass("uiPartDoc_c", 1)
    ):
        raise ValueError(
            "through-all source camera requires its ordinary part Definition"
        )
    FieldsValue = DefinitionValue.DocumentValue.FieldsValue
    return ReadViewPair(FieldsValue.get("fae8"), FieldsValue.get("faf0"))
