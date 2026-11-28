from ntpath import join as JoinPath
from typing import cast as CastValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.SelectPartSelf import KNeutralRoot
from convert.adapters.solidworks.Core.Preparation.Sweeps.PlanSweepPart import (
    PlanSweepPart,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent
from convert.adapters.solidworks.Core.Preparation.Sweeps.SwReadInput import SwReadInput
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Cold.ColdSwSource import (
    IsColdSwSource,
)
from interchange.document.Models.DocumentModel import CadDocument


# discovery and production preparation share the scoped semantic checks and actual file identity rules
def PlanSwTarget(
    DocumentValue: CadDocument,
    TargetValue: KTargetType | None,
    WrittenAt: int,
    SettingsValue: WriteOptions,
) -> SweepIntent:
    NameValue = ReadStyleText(
        DocumentValue.metadata.get("name"), "neutral sweep part name"
    )
    if type(CastValue(object, WrittenAt)) is not int or WrittenAt <= 0:
        raise ValueError("sweep preparation requires positive integer creation time")
    NeutralSelf = SelfFileInput(
        JoinPath(KNeutralRoot, NameValue + ".SLDPRT"), WrittenAt
    )
    NativeSelf = (
        NeutralSelf
        if TargetValue is None
        else FinalPartPath(TargetValue, SettingsValue, NeutralSelf, NameValue)
    )
    InputValue = (
        SwReadInput(DocumentValue)
        if IsColdSwSource(DocumentValue.source)
        else DocumentValue
    )
    IntentValue = PlanSweepPart(InputValue, NativeSelf)
    ConfigValue = DocumentValue.configurations[0]
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested sweep write configuration is unavailable")
    return IntentValue
