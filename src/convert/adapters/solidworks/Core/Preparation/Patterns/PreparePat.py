from dataclasses import replace as ReplaceValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.EmitPatArchive import (
    EmitPatArchive,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatGraph import (
    MakePatGraph,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import (
    PatPresentInput,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.Patterns.PatWritePlan import (
    PatWritePlan,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.CheckPatRead import (
    CheckPatRead,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.PatReadData import (
    IsPatRead,
    PatDocName,
)
from convert.adapters.solidworks.Core.Preparation.SelectPartSelf import KNeutralRoot
from interchange.document.Models.DocumentModel import CadDocument

# an explicit typed presentation belongs to the actual neutral pattern and its driver identities
KPatPresentOpt = "solidworks_pattern_presentation"


# ordinary writer option validation stays shared while the pattern accepts one typed model input
def CheckPatOpts(
    OptionsValue: WriteOptions | None,
) -> tuple[WriteOptions, PatPresentInput | None]:
    if not isinstance(OptionsValue, WriteOptions):
        return CheckPartOpts(OptionsValue), None
    OtherOptions = dict(OptionsValue.values)
    Presentation = OtherOptions.pop(KPatPresentOpt, None)
    if Presentation is not None and type(Presentation) is not PatPresentInput:
        raise TypeError("linear pattern requires an explicit typed presentation")
    return CheckPartOpts(ReplaceValue(OptionsValue, values=OtherOptions)), Presentation


# a scoped model compiles before staged publication reaches either kind of destination
def PreparePat(
    Document: CadDocument,
    Target: KTargetType,
    WrittenAt: int,
    Settings: WriteOptions,
    Presentation: PatPresentInput | None,
) -> bytes:
    NameValue = PatDocName(Document)
    (ConfigValue,) = Document.configurations
    if Settings.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested write configuration is unavailable")
    Recipe = SelfFileInput(KNeutralRoot + "\\" + NameValue + ".SLDPRT", WrittenAt)
    OutputValue = FinalPartPath(Target, Settings, Recipe, NameValue)
    PlanValue = PatWritePlan(Document, OutputValue, Presentation)
    _, Payload = EmitPatArchive(MakePatGraph(PlanValue))
    if IsPatRead(Document):
        CheckPatRead(Document, Payload)
    return Payload
