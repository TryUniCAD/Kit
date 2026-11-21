from convert.adapters.solidworks.Archive.Construction.Configuration.ReadMgrIntent import (
    ReadMgrIntent,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.ThruCfgIntent import (
    ThruCfgIntent,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.Preparation.Revolve.Source.ReadRevUi import (
    ReadRevUi,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.CheckSourceEnv import (
    CheckSourceEnv,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.CheckThruLink import (
    CheckThruLink,
)
from interchange.document.Models.DocumentModel import CadDocument


# a source observation becomes constructor input only after actual model configuration and public identity owners agree
def ReadThruIntent(
    DocumentValue: CadDocument,
    LinkValue: NativeLink,
    ManagerValue: ArchiveNode,
    DefinitionValue: ModelDefGraph,
) -> ThruCfgIntent:
    CheckSourceEnv(DocumentValue)
    CheckThruLink(DocumentValue, LinkValue)
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    IntentValue = ReadMgrIntent(ManagerValue)
    if len(IntentValue.ConfigValues) != 1 or IntentValue.CurrentIndex != 0:
        raise ValueError("source intent requires one actual independent configuration")
    ConfigValue = IntentValue.ConfigValues[0]
    PublicValue = DocumentValue.configurations[0]
    if PublicValue.name != ConfigValue.NameValue:
        raise ValueError(
            "source configuration name differs from its actual manager owner"
        )
    UiValue = ReadRevUi(DefinitionValue)
    return ThruCfgIntent(
        ReadNodeName(ModelValue),
        IntentValue,
        UiValue.SettingsValue,
        UiValue.DensityValue,
    )
