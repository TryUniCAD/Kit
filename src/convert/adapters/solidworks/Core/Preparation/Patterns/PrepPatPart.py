from ntpath import join as JoinPath

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
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.Patterns.PatCandidate import (
    PatCandidate,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.PlanLinPattern import (
    PlanLinPattern,
)
from convert.adapters.solidworks.Core.Preparation.SelectPartSelf import KNeutralRoot
from interchange.document.Models.DocumentModel import CadDocument


# selection and emission must run the same complete graph and archive checks with their own target identity
def PrepPatPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType | None,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
    *,
    PresentValue: PatPresentInput | None = None,
) -> PatCandidate:
    SettingsValue = CheckPartOpts(OptionsValue)
    NameValue = ReadStyleText(DocumentValue.metadata.get("name"), "neutral part name")
    NeutralSelf = SelfFileInput(
        JoinPath(KNeutralRoot, NameValue + ".SLDPRT"), WrittenAt
    )
    NativeSelf = (
        NeutralSelf
        if TargetValue is None
        else FinalPartPath(TargetValue, SettingsValue, NeutralSelf, NameValue)
    )
    PlanValue = PlanLinPattern(DocumentValue, NativeSelf, PresentValue)
    ConfigValue = DocumentValue.configurations[0]
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested pattern write configuration is unavailable")
    _, Payload = EmitPatArchive(MakePatGraph(PlanValue))
    return PatCandidate(Payload)
